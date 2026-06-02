from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import execute_tool_call, tool_results_message
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"
load_lab_env(ROOT)


TOOL_ENV: dict[str, list[str]] = {
    "search_web": ["TAVILY_API_KEY"],
    "read_url": ["FIRECRAWL_API_KEY"],
    "search_social_posts": ["RAPIDAPI_KEY"],
    "get_user_timeline": ["RAPIDAPI_KEY"],
    "send_message": ["TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"],
}

PROVIDER_ENV = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}

EXAMPLES = {
    "Local & Policy": [
        "Theo company policy, tweet viral có được coi là nguồn fact không?",
        "Demo này tập trung vào chủ đề gì?",
        "Theo policy công ty, đăng bản tin lên Telegram có cần xác nhận trước không?",
    ],
    "Research": [
        "Tin AI hôm nay có gì nổi bật?",
        "Tìm 3 paper arXiv mới nhất về retrieval augmented generation",
        "Tóm tắt link này: https://openai.com/research/",
    ],
    "Boundaries": [
        "Tóm tắt 5 tweet mới nhất giúp mình",
        "Đăng bản tin này lên Telegram giúp mình",
        "Viết giúp mình hàm Python tính Fibonacci",
    ],
}


def now_slug() -> str:
    return datetime.now().strftime("%Y%m%dT%H%M%S%f")


def transcript_path() -> Path:
    TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
    if "transcript_path" not in st.session_state:
        st.session_state.transcript_path = str(TRANSCRIPTS_DIR / f"ui_v3_{now_slug()}.transcript.json")
    return Path(st.session_state.transcript_path)


def write_ui_transcript(payload: dict[str, Any]) -> None:
    transcript_path().write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def init_state() -> None:
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("turns", [])


def has_env(name: str) -> bool:
    return bool(os.getenv(name, "").strip())


def env_badge(ok: bool, label: str) -> None:
    if ok:
        st.success(label)
    else:
        st.warning(label)


def tool_health(tool_names: list[str]) -> tuple[list[str], list[str]]:
    ready: list[str] = []
    missing: list[str] = []
    for name in tool_names:
        required = TOOL_ENV.get(name, [])
        absent = [env for env in required if not has_env(env)]
        if absent:
            missing.append(f"{name}: {', '.join(absent)}")
        else:
            ready.append(name)
    return ready, missing


def short_json(value: Any, limit: int = 6000) -> Any:
    text = json.dumps(value, ensure_ascii=False, default=str)
    if len(text) <= limit:
        return value
    return {"truncated": True, "preview": text[:limit]}


def render_sidebar(provider_name: str, version: str, tool_names: list[str]) -> None:
    provider_key = PROVIDER_ENV[provider_name]
    provider_ready = has_env(provider_key)
    _, missing_tools = tool_health(tool_names)

    st.header("Chat Settings")
    env_badge(provider_ready, f"{provider_name} connected")
    if missing_tools:
        with st.expander("Some live tools need keys", expanded=False):
            for item in missing_tools:
                st.caption(item)
    else:
        st.success("Live tools ready")

    st.divider()
    st.subheader("Conversation")
    st.caption("Focus: AI research intelligence")
    path = transcript_path()
    with st.expander("Chat log", expanded=False):
        if not st.session_state.get("messages"):
            st.caption("No messages yet.")
        for index, item in enumerate(st.session_state.get("messages", []), start=1):
            role = "You" if item["role"] == "user" else "Assistant"
            st.markdown(f"**{index}. {role}**")
            st.caption(item["content"])
        st.code(str(path), language="text")
    if path.exists():
        st.download_button(
            "Download transcript",
            data=path.read_text(encoding="utf-8"),
            file_name=path.name,
            mime="application/json",
            use_container_width=True,
        )


def render_examples() -> None:
    st.subheader("Try A Scenario")
    tabs = st.tabs(list(EXAMPLES))
    for tab, prompts in zip(tabs, EXAMPLES.values()):
        with tab:
            for prompt in prompts:
                if st.button(prompt, use_container_width=True):
                    st.session_state.pending_prompt = prompt
                    st.rerun()


def run_tool_loop(
    *,
    provider: Any,
    messages: list[dict[str, str]],
    openai_tools: list[dict[str, Any]],
    model: str | None,
    max_tool_rounds: int,
) -> tuple[str, list[dict[str, Any]]]:
    working_messages = list(messages)
    rounds: list[dict[str, Any]] = []
    tool_events: list[dict[str, Any]] = []
    final_text = ""

    for round_index in range(1, max_tool_rounds + 1):
        response = provider.complete(
            working_messages,
            openai_tools,
            model=model,
            temperature=0.0,
        )
        calls = response.tool_calls
        round_record = {
            "round": round_index,
            "assistant_text": response.text,
            "tool_calls": [{"name": call.name, "args": call.args} for call in calls],
            "tool_results": [],
        }

        if not calls:
            final_text = response.text or ""
            rounds.append(round_record)
            break

        visible_events: list[dict[str, Any]] = []
        for call in calls:
            event = execute_tool_call(call)
            tool_events.append(event)
            visible_events.append(event)
            round_record["tool_results"].append(event)

            result = event.get("result", {})
            if isinstance(result, dict) and result.get("awaiting_user"):
                final_text = result.get("question") or call.args.get("question") or "Please add the missing information."
                break

        rounds.append(round_record)
        if final_text:
            break
        working_messages.append(tool_results_message(visible_events))

    if not final_text:
        final_text = "I reached the tool-round limit. Please inspect the tool timeline."
    return final_text, rounds


def main() -> None:
    st.set_page_config(page_title="AI Research Intelligence", page_icon="AI", layout="centered")
    init_state()

    system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
    tools_path = ARTIFACTS_DIR / "tools.yaml"
    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    tool_names = [tool["name"] for tool in tool_declarations]

    with st.sidebar:
        st.header("Settings")
        provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
        with st.expander("Advanced", expanded=False):
            model = st.text_input("Model override", value="", placeholder="Leave blank for provider default")
            version = st.text_input("Internal version", value="v3")
            max_tool_rounds = st.slider("Max tool rounds", 1, 4, 3)
        render_sidebar(provider_name, version, tool_names)
        st.divider()
        if st.button("Reset chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.turns = []
            st.session_state.pop("transcript_path", None)
            st.rerun()

    provider = make_provider(provider_name)
    selected_model = model.strip() or None
    artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

    st.title("AI Research Intelligence")
    st.caption("Ask about AI news, papers, social signals, source policy, URLs, or safe publishing.")

    render_examples()

    if not st.session_state.messages:
        with st.chat_message("assistant"):
            st.markdown(
                "Ask me to monitor AI research, search papers, inspect source policy, read a URL, "
                "or test a safe publishing boundary. I will ask for missing details instead of guessing."
            )

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask about AI research, news, papers, social signals, URLs, or policy")
    prompt = st.session_state.pop("pending_prompt", None) or prompt
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    turn_record: dict[str, Any] = {
        "user": prompt,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "rounds": [],
    }
    messages = [{"role": "system", "content": system_prompt}, *st.session_state.messages]

    with st.chat_message("assistant"):
        with st.spinner("Choosing tools and collecting evidence..."):
            try:
                final_text, rounds = run_tool_loop(
                    provider=provider,
                    messages=messages,
                    openai_tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds,
                )
                turn_record["rounds"] = rounds
            except Exception as exc:
                final_text = f"Provider error: {type(exc).__name__}: {exc}"
                turn_record["error"] = final_text

        st.markdown(final_text)

        tool_calls = [call for round_item in turn_record.get("rounds", []) for call in round_item.get("tool_calls", [])]
        if tool_calls:
            with st.expander("Tool timeline", expanded=True):
                for index, round_item in enumerate(turn_record["rounds"], start=1):
                    st.markdown(f"**Round {index}**")
                    calls = round_item.get("tool_calls", [])
                    results = round_item.get("tool_results", [])
                    if not calls:
                        st.caption("No tool call")
                    for call, result in zip(calls, results):
                        st.code(f"{call['name']}({json.dumps(call['args'], ensure_ascii=False)})", language="text")
                        st.json(short_json(result.get("result")))

    st.session_state.messages.append({"role": "assistant", "content": final_text})
    turn_record.update({
        "assistant": final_text,
        "ended_at": datetime.now().isoformat(timespec="seconds"),
    })
    st.session_state.turns.append(turn_record)
    write_ui_transcript({
        "transcript_id": transcript_path().stem,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": selected_model or getattr(provider, "default_model", None),
        "ui": "streamlit",
        "topic": "AI research intelligence",
        "turns": st.session_state.turns,
    })


if __name__ == "__main__":
    main()
