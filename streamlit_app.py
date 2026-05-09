import streamlit as st
import numpy as np
import pandas as pd
from scipy import stats

st.set_page_config(
    page_title="Experiment Decision Simulator",
    page_icon="🧪",
    layout="wide",
)

st.title("🧪 Experiment Decision Simulator")
st.markdown(
    "**Turn A/B test results into rollout decisions, not just p-values.**  \n"
    "Simulate an experiment or upload your results to get a "
    "structured SHIP / DO NOT SHIP recommendation."
)
st.divider()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Experiment Setup")

    mode = st.radio("Mode", ["🎛️ Simulate experiment", "📤 Upload results CSV"])

    if mode == "🎛️ Simulate experiment":
        st.markdown("**Users**")
        n_total   = st.slider("Total Users", 1_000, 200_000, 50_000, step=1_000)
        split_pct = st.slider("Treatment Traffic Split (%)", 10, 90, 50)

        st.markdown("**Conversion**")
        ctrl_cr   = st.slider("Control Conversion Rate (%)", 0.5, 40.0, 10.0, step=0.5) / 100
        lift_pct  = st.slider("True Treatment Lift (%)", -50, 100, 20) / 100
        treat_cr  = ctrl_cr * (1 + lift_pct)

        st.markdown("**Revenue**")
        rev_per_conv = st.number_input("Revenue per Conversion ($)", 1.0, 5000.0, 50.0, step=1.0)

        st.markdown("**Statistics**")
        confidence = st.selectbox("Confidence Level", [0.90, 0.95, 0.99], index=1)
        alpha      = 1 - confidence

        st.markdown("**Guardrail Metric**")
        guardrail = st.selectbox(
            "Guardrail", ["None", "Page Load Time", "Error Rate", "Session Duration"]
        )
        guardrail_breached = False
        if guardrail != "None":
            guardrail_breached = st.checkbox(f"{guardrail} degraded in treatment?")

    run_btn = st.button("▶ Run Analysis", type="primary", use_container_width=True)

# ── Landing state ─────────────────────────────────────────────────────────────
if not run_btn:
    st.markdown(
        """
        ### How this works
        1. Set experiment parameters using the sidebar controls
        2. Click **Run Analysis**
        3. The simulator generates control and treatment groups, runs a z-test for
           proportions, and produces a structured decision
        4. The decision includes: statistical result, revenue impact, guardrail check,
           and a rollout recommendation — not just a p-value

        ### Why this matters
        Most A/B testing notebooks stop at significance. This tool adds the layer
        that actually drives a product decision: what to do with the result.

        ### Upload mode
        Switch to **Upload results CSV** and upload a file with columns:
        `group` (control/treatment), `converted` (0/1), `revenue` (optional)
        """
    )
    st.stop()

# ── Simulate ──────────────────────────────────────────────────────────────────
if mode == "🎛️ Simulate experiment":
    np.random.seed(42)
    n_ctrl  = int(n_total * (1 - split_pct / 100))
    n_treat = int(n_total * (split_pct / 100))

    ctrl_conv  = int(np.random.binomial(n_ctrl, ctrl_cr))
    treat_conv = int(np.random.binomial(n_treat, treat_cr))

    obs_ctrl_cr  = ctrl_conv  / n_ctrl  if n_ctrl  > 0 else 0
    obs_treat_cr = treat_conv / n_treat if n_treat > 0 else 0
    obs_lift     = (obs_treat_cr - obs_ctrl_cr) / obs_ctrl_cr if obs_ctrl_cr > 0 else 0

    pooled_p = (ctrl_conv + treat_conv) / (n_ctrl + n_treat)
    se       = np.sqrt(pooled_p * (1 - pooled_p) * (1/n_ctrl + 1/n_treat))
    z_stat   = (obs_treat_cr - obs_ctrl_cr) / se if se > 0 else 0
    p_value  = float(2 * (1 - stats.norm.cdf(abs(z_stat))))

    z_crit  = stats.norm.ppf(1 - alpha / 2)
    margin  = z_crit * se
    ci_low  = obs_treat_cr - obs_ctrl_cr - margin
    ci_high = obs_treat_cr - obs_ctrl_cr + margin

    rev_impact  = (obs_treat_cr - obs_ctrl_cr) * n_treat * rev_per_conv
    is_sig      = p_value < alpha
    is_positive = obs_treat_cr >= obs_ctrl_cr

    if guardrail_breached:
        decision     = "⚠️ HOLD — GUARDRAIL BREACH"
        badge        = "warning"
        rec = (
            f"Treatment shows {'positive' if is_positive else 'negative'} lift, "
            f"but **{guardrail}** is degraded. Do not ship until resolved."
        )
    elif is_sig and is_positive:
        decision = "✅ SHIP"
        badge    = "success"
        rec      = "Statistically significant positive lift. Recommend full rollout."
    elif is_sig and not is_positive:
        decision = "🚫 DO NOT SHIP"
        badge    = "error"
        rec      = "Statistically significant negative impact. Roll back treatment."
    elif not is_sig and is_positive:
        decision = "🔄 EXTEND EXPERIMENT"
        badge    = "info"
        rec = (
            f"Positive trend not yet significant at {confidence:.0%}. "
            "Increase sample size or extend duration."
        )
    else:
        decision = "🔄 INCONCLUSIVE"
        badge    = "info"
        rec      = "No significant effect. Re-evaluate the hypothesis or experiment design."

    # Results
    st.subheader("Results")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Control CR",   f"{obs_ctrl_cr:.2%}")
    c2.metric("Treatment CR", f"{obs_treat_cr:.2%}", f"{obs_lift:+.1%}")
    c3.metric("P-Value",      f"{p_value:.4f}",       f"α = {alpha}")
    c4.metric("Revenue Lift", f"${rev_impact:+,.0f}")

    if badge == "success":
        st.success(f"### Decision: {decision}")
    elif badge == "error":
        st.error(f"### Decision: {decision}")
    elif badge == "warning":
        st.warning(f"### Decision: {decision}")
    else:
        st.info(f"### Decision: {decision}")

    st.markdown(f"**Recommendation:** {rec}")
    st.markdown(
        f"**{confidence:.0%} CI for absolute lift:** "
        f"[{ci_low:+.2%},  {ci_high:+.2%}]"
    )
    st.divider()

    # Stats table
    st.subheader("Statistical Detail")
    stats_table = pd.DataFrame({
        "Metric": [
            "Control users", "Treatment users",
            "Control conversions", "Treatment conversions",
            "Z-statistic", "P-value",
            f"Significant at {confidence:.0%}?",
        ],
        "Value": [
            f"{n_ctrl:,}", f"{n_treat:,}",
            f"{ctrl_conv:,}", f"{treat_conv:,}",
            f"{z_stat:.4f}", f"{p_value:.4f}",
            "Yes" if is_sig else "No",
        ],
    })
    st.dataframe(stats_table, use_container_width=True, hide_index=True)
    st.divider()

    # Sample size reference table
    st.subheader("Sample Size Requirements")
    st.caption("Users per variant needed to detect a given lift at 80% power")
    z_power    = stats.norm.ppf(0.80)
    power_rows = []
    for mde in [0.05, 0.10, 0.15, 0.20, 0.30]:
        treat_p = ctrl_cr * (1 + mde)
        p_avg   = (ctrl_cr + treat_p) / 2
        denom   = (treat_p - ctrl_cr) ** 2
        n_req   = (
            int(2 * (z_crit + z_power) ** 2 * p_avg * (1 - p_avg) / denom)
            if denom > 0 else "—"
        )
        power_rows.append({
            "Min Detectable Lift": f"{mde:.0%}",
            "Required Users Per Variant": f"{n_req:,}" if isinstance(n_req, int) else n_req,
        })
    st.dataframe(pd.DataFrame(power_rows), use_container_width=True, hide_index=True)

    # Download memo
    memo = f"""EXPERIMENT DECISION MEMO
{"=" * 60}

EXPERIMENT PARAMETERS
Total users:         {n_total:,}
Traffic split:       {split_pct}% treatment
Control CR:          {obs_ctrl_cr:.2%}
Treatment CR:        {obs_treat_cr:.2%}
Observed lift:       {obs_lift:+.1%}

STATISTICAL RESULTS
Z-statistic:         {z_stat:.4f}
P-value:             {p_value:.4f}
Confidence level:    {confidence:.0%}
{confidence:.0%} CI for lift:    [{ci_low:+.2%}, {ci_high:+.2%}]
Significant:         {"Yes" if is_sig else "No"}

GUARDRAIL
{guardrail}: {"BREACHED ⚠️" if guardrail_breached else "OK ✅"}

REVENUE IMPACT
Estimated lift vs control: ${rev_impact:+,.2f}

DECISION: {decision}

RECOMMENDATION
{rec}

{"=" * 60}
"""
    st.divider()
    st.download_button(
        "⬇️ Download Decision Memo",
        data=memo,
        file_name="experiment_decision_memo.txt",
        mime="text/plain",
        use_container_width=True,
    )

else:
    # Upload mode
    uploaded = st.file_uploader("Upload results CSV", type=["csv"])
    if uploaded is None:
        st.info(
            "Upload a CSV with columns: `group` (control/treatment), "
            "`converted` (0/1), `revenue` (optional)"
        )
        st.stop()

    data      = pd.read_csv(uploaded)
    required  = {"group", "converted"}
    if not required.issubset(data.columns):
        st.error(f"CSV must have columns: {required}")
        st.stop()

    ctrl  = data[data["group"] == "control"]
    treat = data[data["group"] == "treatment"]

    n_ctrl, n_treat = len(ctrl), len(treat)
    ctrl_conv  = ctrl["converted"].sum()
    treat_conv = treat["converted"].sum()

    obs_ctrl_cr  = ctrl_conv  / n_ctrl  if n_ctrl  > 0 else 0
    obs_treat_cr = treat_conv / n_treat if n_treat > 0 else 0
    obs_lift     = (obs_treat_cr - obs_ctrl_cr) / obs_ctrl_cr if obs_ctrl_cr > 0 else 0

    pooled_p = (ctrl_conv + treat_conv) / (n_ctrl + n_treat)
    se       = np.sqrt(pooled_p * (1-pooled_p) * (1/n_ctrl + 1/n_treat))
    z_stat   = (obs_treat_cr - obs_ctrl_cr) / se if se > 0 else 0
    p_value  = float(2 * (1 - stats.norm.cdf(abs(z_stat))))

    st.subheader("Results")
    c1, c2, c3 = st.columns(3)
    c1.metric("Control CR",   f"{obs_ctrl_cr:.2%}")
    c2.metric("Treatment CR", f"{obs_treat_cr:.2%}", f"{obs_lift:+.1%}")
    c3.metric("P-Value",      f"{p_value:.4f}",       "α = 0.05")

    if p_value < 0.05 and obs_treat_cr > obs_ctrl_cr:
        st.success("### Decision: ✅ SHIP — Significant positive lift")
    elif p_value < 0.05:
        st.error("### Decision: 🚫 DO NOT SHIP — Significant negative impact")
    else:
        st.info("### Decision: 🔄 INCONCLUSIVE — Not significant at 95%")