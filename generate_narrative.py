import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def generate_scr_narrative_offline(findings: dict) -> dict:
    pay = findings["return_rate_by_payment"]
    risk = findings["highest_risk_segment"]
    peak = findings["true_peak_month"]
    inflated = findings["outlier_inflated_month"]
    narrative = f"""Situation
The cleaned order pipeline reports total revenue of {findings['cleaned_total_revenue_inr']:,.2f} INR across deduplicated orders. The raw SQL layer reports {findings['raw_total_revenue_inr']:,.2f} INR before duplicate removal.

Complication
Returns are concentrated in Cash on Delivery (COD): COD return rate is {pay['COD']:.1f}%, compared with {pay['CARD']:.1f}% for CARD and {pay['UPI']:.1f}% for UPI. The highest-risk segment is COD in Tier-{risk['city_tier']} cities, with a {risk['return_rate_pct']:.1f}% return rate. The raw-to-cleaned revenue difference is {findings['duplicate_reconciliation_delta_inr']:,.2f} INR, explained by duplicate orders. January appeared to lead at {inflated['apparent_revenue_inr']:,.2f} INR, but bulk-order outliers inflate that figure.

Resolution
Prioritize COD controls and return-reason reviews in Tier-{risk['city_tier']} cities, then monitor results by payment method and city tier. Use the outlier-corrected trend for planning: {peak['month']} is the true peak month at {peak['revenue_inr']:,.2f} INR. Keep the duplicate-detection and reconciliation checks in the repeatable pipeline."""
    return {"status":"success","narrative":narrative,"tokens":None}

def generate_scr_narrative(findings: dict) -> dict:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return generate_scr_narrative_offline(findings)
    try:
        from google import genai
        client = genai.Client(api_key=api_key, http_options={"timeout": 30000})
        system_instruction = (
            "You are a senior data analyst writing for Mamaearth's regional ops and finance heads. "
            "Write exactly three labeled sections: Situation, Complication, Resolution. "
            "Every number must come only from the supplied findings and appear with the same value; "
            "do not invent statistics."
        )
        prompt = "Write a concise business narrative using these verified findings:\n" + json.dumps(findings, indent=2)
        # Temperature 0.0 is used because this is a factual business report, not creative writing.
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"system_instruction":system_instruction,"temperature":0.0,"max_output_tokens":600,"http_options":{"timeout":30000}}
        )
        return {"status":"success","narrative":response.text,"tokens":getattr(getattr(response,"usage_metadata",None),"total_token_count",None)}
    except Exception as err:
        result = generate_scr_narrative_offline(findings)
        result["message"] = str(err)
        result["fallback"] = "offline"
        return result

def check_numeric_accuracy(narrative: str) -> bool:
    normalized = narrative.replace(",", "")
    checks = [
        ("cleaned revenue", "97358.3"),
        ("COD return rate", "44.4"),
        ("COD Tier-2 risk", "54.5"),
        ("duplicate delta", "2501.9"),
        ("March peak revenue", "20318.9"),
    ]
    ok_all=True
    for label, needle in checks:
        ok = needle in normalized
        print(f"{'PASS' if ok else 'FAIL'}: {label} ({needle})")
        ok_all &= ok
    return ok_all

def main():
    findings_path=ROOT/"narrator"/"findings.json"
    findings=json.loads(findings_path.read_text())
    result=generate_scr_narrative(findings)
    narrative=result.get("narrative") or ""
    print(json.dumps({k:v for k,v in result.items() if k!="narrative"},indent=2))
    print(narrative)
    (ROOT/"narrator"/"sample_output.txt").write_text(narrative+"\n")
    check_numeric_accuracy(narrative)

if __name__=="__main__":
    main()
