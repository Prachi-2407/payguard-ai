import pytest
from extras.app.analyzers.message_analyzer import MessageAnalyzer
from extras.app.analyzers.voice_analyzer import VoiceAnalyzer

@pytest.mark.asyncio
async def test_sample_messages_results_table(sample_messages, db_session):
    """
    Evaluates all 25 sample messages in sample_data/extras/messages.json
    and prints a formatted results table comparing expected vs predicted risk.
    """
    analyzer = MessageAnalyzer()
    results = []

    print("\n" + "=" * 90)
    print(f"{'ID':<14} | {'SOURCE':<8} | {'EXP LEVEL':<10} | {'PRED LEVEL':<10} | {'PRED CAT':<18} | {'SCORE':<5} | {'MATCH'}")
    print("=" * 90)

    for item in sample_messages:
        mid = item["id"]
        msg = item["message"]
        src = item["source"]
        exp_level = item["expected_risk_level"]
        exp_cat = item["expected_category"]

        res = await analyzer.analyze(msg, source=src, db=db_session)
        pred_level = res.risk_level
        pred_cat = res.extracted.scam_category
        score = res.risk_score

        # Rule from prompt: All scam messages must be MEDIUM or HIGH, safe messages must be LOW
        if exp_level == "LOW":
            level_match = (pred_level == "LOW")
        else:
            level_match = (pred_level in ("MEDIUM", "HIGH"))

        match_str = "PASS" if level_match else "FAIL"
        print(f"{mid:<14} | {src:<8} | {exp_level:<10} | {pred_level:<10} | {pred_cat:<18} | {score:<5} | {match_str}")

        results.append({
            "id": mid,
            "exp_level": exp_level,
            "pred_level": pred_level,
            "score": score,
            "pass": level_match,
        })

    print("=" * 90)

    # Assert 100% pass on risk levels
    failures = [r for r in results if not r["pass"]]
    assert len(failures) == 0, f"Sample messages failed expected risk level: {failures}"

@pytest.mark.asyncio
async def test_sample_voice_transcripts_results_table(sample_voices, db_session):
    """
    Evaluates all sample voice transcripts in sample_data/extras/voice_transcripts.json
    and prints a formatted results table.
    """
    analyzer = VoiceAnalyzer()
    results = []

    print("\n" + "=" * 90)
    print(f"{'ID':<14} | {'LANG':<5} | {'EXP LEVEL':<10} | {'PRED LEVEL':<10} | {'PRED CAT':<30} | {'SCORE':<5} | {'MATCH'}")
    print("=" * 90)

    for item in sample_voices:
        vid = item["id"]
        transcript = item["transcript"]
        lang = item.get("language", "en")
        exp_level = item["expected_risk_level"]
        exp_cat = item["expected_category"]

        res = await analyzer.analyze(transcript, db=db_session)
        pred_level = res.risk_level
        pred_cat = res.scam_category
        score = res.risk_score

        if exp_level == "LOW":
            level_match = (pred_level == "LOW")
        else:
            level_match = (pred_level in ("MEDIUM", "HIGH"))

        match_str = "PASS" if level_match else "FAIL"
        print(f"{vid:<14} | {lang:<5} | {exp_level:<10} | {pred_level:<10} | {pred_cat:<30} | {score:<5} | {match_str}")

        results.append({
            "id": vid,
            "exp_level": exp_level,
            "pred_level": pred_level,
            "score": score,
            "pass": level_match,
        })

    print("=" * 90)

    failures = [r for r in results if not r["pass"]]
    assert len(failures) == 0, f"Sample voice transcripts failed expected risk level: {failures}"

