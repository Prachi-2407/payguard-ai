// src/hooks/useQrScanner.js
import { useState, useRef, useCallback, useEffect } from 'react';
import jsQR from 'jsqr';

export function parseUpiPayload(payload) {
  if (!payload) return null;
  const trimmed = payload.trim();
  if (trimmed.toLowerCase().startsWith('upi://pay')) {
    try {
      const url = new URL(trimmed);
      return {
        type: 'upi',
        raw: trimmed,
        pa: url.searchParams.get('pa') || '',
        pn: url.searchParams.get('pn') || '',
        am: url.searchParams.get('am') || '',
        cu: url.searchParams.get('cu') || 'INR',
        tn: url.searchParams.get('tn') || '',
        mc: url.searchParams.get('mc') || '',
        tr: url.searchParams.get('tr') || '',
      };
    } catch (e) {
      return { type: 'upi_malformed', raw: trimmed };
    }
  } else if (trimmed.toLowerCase().startsWith('http://') || trimmed.toLowerCase().startsWith('https://')) {
    return { type: 'url', raw: trimmed, url: trimmed };
  }
  return { type: 'text', raw: trimmed };
}

export function useQrScanner() {
  const [isScanning, setIsScanning] = useState(false);
  const [cameraError, setCameraError] = useState(null);
  const [decodedData, setDecodedData] = useState(null);
  const [parsedPayload, setParsedPayload] = useState(null);

  const videoRef = useRef(null);
  const animationFrameRef = useRef(null);
  const streamRef = useRef(null);

  const stopCamera = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsScanning(false);
  }, []);

  const scanFrame = useCallback(() => {
    const video = videoRef.current;
    if (!video || video.readyState !== video.HAVE_ENOUGH_DATA) {
      animationFrameRef.current = requestAnimationFrame(scanFrame);
      return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) {
      animationFrameRef.current = requestAnimationFrame(scanFrame);
      return;
    }

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const code = jsQR(imageData.data, imageData.width, imageData.height, {
      inversionAttempts: 'dontInvert',
    });

    if (code && code.data) {
      setDecodedData(code.data);
      setParsedPayload(parseUpiPayload(code.data));
      stopCamera();
    } else {
      animationFrameRef.current = requestAnimationFrame(scanFrame);
    }
  }, [stopCamera]);

  const startCamera = useCallback(async () => {
    setCameraError(null);
    setDecodedData(null);
    setParsedPayload(null);
    setIsScanning(true);

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Webcam not supported or not available in this browser environment.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.setAttribute('playsinline', 'true');
        videoRef.current.play();
        animationFrameRef.current = requestAnimationFrame(scanFrame);
      }
    } catch (err) {
      let message = 'Unable to access camera.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        message = 'Camera permission was denied. Please allow camera permissions in browser settings.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        message = 'No camera device found on this system. You can upload a QR image below.';
      } else {
        message = err.message || message;
      }
      setCameraError(message);
      setIsScanning(false);
    }
  }, [scanFrame]);

  const scanImageFile = useCallback((file) => {
    return new Promise((resolve, reject) => {
      setCameraError(null);
      if (!file) return;

      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          if (!ctx) {
            reject(new Error('Failed to create canvas context'));
            return;
          }
          ctx.drawImage(img, 0, 0);
          const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
          const code = jsQR(imageData.data, imageData.width, imageData.height);
          if (code && code.data) {
            setDecodedData(code.data);
            const parsed = parseUpiPayload(code.data);
            setParsedPayload(parsed);
            resolve({ raw: code.data, parsed });
          } else {
            const noQrErr = new Error('No valid QR code detected in the selected image. Please try another image.');
            setCameraError(noQrErr.message);
            reject(noQrErr);
          }
        };
        img.onerror = () => {
          const loadErr = new Error('Failed to load image file.');
          setCameraError(loadErr.message);
          reject(loadErr);
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    });
  }, []);

  const setManualPayload = useCallback((payloadStr) => {
    setDecodedData(payloadStr);
    setParsedPayload(parseUpiPayload(payloadStr));
  }, []);

  const resetScanner = useCallback(() => {
    stopCamera();
    setDecodedData(null);
    setParsedPayload(null);
    setCameraError(null);
  }, [stopCamera]);

  useEffect(() => {
    return () => {
      stopCamera();
    };
  }, [stopCamera]);

  return {
    isScanning,
    cameraError,
    decodedData,
    parsedPayload,
    videoRef,
    startCamera,
    stopCamera,
    scanImageFile,
    setManualPayload,
    resetScanner,
  };
}

