%%writefile app.py
import os
import math
from groq import Groq
import streamlit as st

# ---- Page setup (HCI: clear, centered, friendly) ----
st.set_page_config(
    page_title="Smart Calculator (Groq-powered)",
    page_icon="🧮",
    layout="centered"
)

st.title("🧮 Smart Calculator")
st.caption("A simple calculator with AI explanations and natural language support (Groq LLM).")

# ---- Session state for history ----
if "history" not in st.session_state:
    st.session_state["history"] = []  # list of dicts: {expression, result}


# ---- Helper functions ----

def create_groq_client():
    """Create a Groq client using the API key from environment variable."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return None, "GROQ_API_KEY is missing. Set it in Colab secrets and environment."
    try:
        client = Groq(api_key=api_key)
        return client, None
    except Exception as e:
        return None, f"Error creating Groq client: {e}"


def calculate(a, b, op_label):
    """Perform the selected arithmetic operation."""
    if op_label == "Add (+)":
        return a + b, "+"
    elif op_label == "Subtract (-)":
        return a - b, "-"
    elif op_label == "Multiply (×)":
        return a * b, "×"
    elif op_label == "Divide (÷)":
        if b == 0:
            raise ZeroDivisionError("Cannot divide by zero.")
        return a / b, "÷"
    elif op_label == "Power (a^b)":
        return a ** b, "^"
    elif op_label == "Percentage (a% of b)":
        # "a percent of b" -> (a / 100) * b
        return (a / 100.0) * b, "% of"
    else:
        raise ValueError("Unknown operation selected.")


def add_to_history(expression, result):
    """Store a calculation in history (latest on top, max 10 items)."""
    st.session_state["history"].insert(0, {
        "expression": expression,
        "result": result
    })
    # limit size
    st.session_state["history"] = st.session_state["history"][:10]


# ---- Sidebar: History panel (HCI: always visible context) ----
with st.sidebar:
    st.header("📜 History")
    if st.session_state["history"]:
        for item in st.session_state["history"]:
            st.write(f"{item['expression']} = **{item['result']}**")
        if st.button("🧹 Clear history"):
            st.session_state["history"] = []
            st.experimental_rerun()
    else:
        st.info("No calculations yet.")


# =========================
# 1️⃣ BASIC CALCULATOR
# =========================

st.markdown("---")
st.header("1️⃣ Basic Calculator")

col1, col2 = st.columns(2)

with col1:
    num1 = st.number_input("First number", value=0.0, format="%.6f")
with col2:
    num2 = st.number_input("Second number", value=0.0, format="%.6f")

operation = st.selectbox(
    "Choose operation",
    [
        "Add (+)",
        "Subtract (-)",
        "Multiply (×)",
        "Divide (÷)",
        "Power (a^b)",
        "Percentage (a% of b)",
    ]
)

calc_button = st.button("✅ Calculate")

if "last_calc" not in st.session_state:
    st.session_state["last_calc"] = None

if calc_button:
    try:
        result, symbol = calculate(num1, num2, operation)

        # Build a human-readable expression string
        if symbol == "% of":
            expression = f"{num1}% of {num2}"
        else:
            expression = f"{num1} {symbol} {num2}"

        st.success(f"Result: {expression} = {result}")

        # Store last calculation and add to history
        st.session_state["last_calc"] = {
            "num1": num1,
            "num2": num2,
            "symbol": symbol,
            "result": result,
            "expression": expression,
        }
        add_to_history(expression, result)

    except ZeroDivisionError as zde:
        st.error(f"⚠️ {zde}")
        st.session_state["last_calc"] = None
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.session_state["last_calc"] = None


st.markdown("---")

# =========================
# 2️⃣ AI EXPLANATION OF LAST CALC
# =========================

st.header("2️⃣ Ask Groq to Explain the Last Calculation")

if st.session_state["last_calc"] is None:
    st.info("First perform a calculation above, then you can ask Groq to explain it.")
else:
    lc = st.session_state["last_calc"]
    default_prompt = (
        f"Explain step by step how to compute {lc['expression']} "
        f"to get {lc['result']}. Use simple language for a beginner."
    )

    user_prompt = st.text_area(
        "Optional: customize the question you want to ask the AI",
        value=default_prompt,
        height=120
    )

    explain_button = st.button("🤖 Explain this calculation with AI (Groq)")

    if explain_button:
        client, err = create_groq_client()
        if err:
            st.error(f"❌ {err}")
        else:
            with st.spinner("Asking Groq to explain..."):
                try:
                    # Your exact Groq usage style
                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": user_prompt,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                    )

                    explanation = chat_completion.choices[0].message.content
                    st.subheader("AI Explanation")
                    st.write(explanation)

                except Exception as e:
                    st.error(f"Error while contacting Groq: {e}")


st.markdown("---")

# =========================
# 3️⃣ NATURAL LANGUAGE CALCULATOR (AI)
# =========================

st.header("3️⃣ Natural Language Calculator (AI)")

st.write(
    "Type a math question in plain English, e.g. "
    "_\"What is 12 divided by 3 plus 4?\"_. The AI will solve it and explain."
)

nl_question = st.text_input(
    "Your question:",
    value="What is 12 divided by 3 plus 4?",
    placeholder="Type a math question in natural language..."
)

ask_ai_button = st.button("🧠 Ask AI to Calculate")

if ask_ai_button:
    if not nl_question.strip():
        st.warning("Please enter a question first.")
    else:
        client, err = create_groq_client()
        if err:
            st.error(f"❌ {err}")
        else:
            with st.spinner("Asking Groq to solve your question..."):
                try:
                    # Prompt Groq to act as a calculator + explainer
                    prompt = (
                        "You are a careful math tutor. Solve the following math question, "
                        "then give the final numeric answer and explain it step by step "
                        "in very simple language for a beginner.\n\n"
                        f"Question: {nl_question}"
                    )

                    chat_completion = client.chat.completions.create(
                        messages=[
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        model="llama-3.3-70b-versatile",
                    )

                    answer_text = chat_completion.choices[0].message.content
                    st.subheader("AI Answer")
                    st.write(answer_text)

                except Exception as e:
                    st.error(f"Error while contacting Groq: {e}")

st.caption(
    "Designed with HCI principles: clear layout, visible history, friendly messages, "
    "and step-by-step AI explanations."
)
