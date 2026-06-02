# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: Team 5 - Zone 7
- Members: Lã Duy Anh-2A202600869, Phạm Văn Mạnh-2A202600837
- Provider/model: OpenRouter / `openai/gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent này tập trung vào AI research intelligence: tìm tin AI, tìm paper/arXiv, đọc URL, theo dõi social signals, kiểm tra policy nội bộ về source/publishing, tổng hợp digest và chỉ gửi ra Telegram khi có xác nhận rõ ràng.

**Link dùng thử (deploy):**

> Dán link public để team khác mở thử ngay. Cách deploy nhanh bằng Cloudflare Tunnel xem README. Nếu deploy Vercel/Streamlit Cloud thì dán link đó.
>
> URL: `https://dad-searching-built-cosmetics.trycloudflare.com`

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `ask_user` | Hỏi lại người dùng khi thiếu topic/account/URL hoặc cần xác nhận yes/no trước hành động gửi/đăng. | Không |
| `get_user_timeline` | Lấy bài đăng/tweet gần đây từ một account cụ thể. | Không |
| `search_social_posts` | Tìm social posts/tweets về một chủ đề cụ thể. | Không |
| `search_web` | Tìm web/news theo query, topic và timeframe. | Không |
| `read_url` | Đọc nội dung từ một URL cụ thể. | Không |
| `render_digest` | Format các item đã thu thập thành bản digest Markdown. | Không |
| `send_message` | Gửi message ra Telegram, chỉ dùng sau khi user xác nhận rõ ràng. | Không |
| `search_policy` | Tìm trong policy markdown nội bộ của công ty. | Không |
| `search_papers` | Tìm paper/arXiv theo query, số lượng và kiểu sắp xếp. | Không |
| `read_paper_text` | Lấy text từ một arXiv paper ID/URL. | Không |
| `search_topic_notes` | Tìm trong file focus topic của demo: AI Research Intelligence. | Có |

## A3. Câu hỏi mẫu để thử

1. `Demo tập trung vào vấn đề gì?`
2. `Theo company policy, tweet viral có được coi là nguồn fact không?`
3. `Theo policy công ty, đăng bản tin lên Telegram có cần xác nhận trước không?`
4. `Tìm 3 paper arXiv mới nhất về retrieval augmented generation`
5. `Đăng bản tin này lên Telegram giúp mình`

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Starter prompt encourages guessing and unsafe actions, so missing-info/boundary cases will fail. |  | 0.70 | `runs/v0_B_base_openrouter_20260602T122900619405.json` |
| v1 | `artifacts/system_prompt.md` + `artifacts/tools.yaml` | Clear routing and tool descriptions should fix wrong tool calls and guessing. | 0.70 | 0.95 | `runs/v1_B_base_openrouter_20260602T123609390728.json` |
| v2 | `artifacts/system_prompt.md` + `artifacts/tools.yaml` | Explicit yes/no confirmation guidance should fix Telegram confirmation argument. | 0.95 | 0.90 | `runs/v2_B_base_openrouter_20260602T123740900757.json` |
| v3 | `artifacts/system_prompt.md` + `artifacts/tools.yaml` + tool names + UI + `search_topic_notes` | Verb-first tool names plus a narrow topic-notes tool should preserve routing while making the demo clearer. | 0.90 | 1.00 | `runs/v3_B_base_openrouter_20260602T140746798127.json` |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| `R08_out_of_scope` | `out_of_scope` | `send_message(...)` in v0 equivalent behavior | v0 used an action tool for a math/general request. | Added no-tool boundary for non-research, math, coding and general assistant tasks. |
| `R10_missing_handle` | `missing_info` | `get_user_timeline(screenname="sama")` in v0 equivalent behavior | v0 guessed Sam Altman when the user did not provide an account. | Added missing-handle rule: call `ask_user(response_type="text")`. |
| `R11_missing_url` | `missing_info` | `read_url(url="https://example.com/article")` in v0 equivalent behavior | v0 invented a URL for "this article". | Added missing-URL rule and exact URL constraint. |
| `R12_confirm_before_send` | `wrong_boundary` | `send_message(...)`, later `ask_user(response_type="text")` | v0 sent immediately; v1/v2 asked for text instead of yes/no confirmation. | Added direct Telegram confirmation example with `ask_user(response_type="yes_no")`. |
| `R13_parallel_web_and_tweets` | `wrong_tool` | `search_web(...)` + wrong account timeline in v0 equivalent behavior | v0 confused tweets ABOUT a topic with tweets FROM an account. | Clarified account timeline vs topic social search. |
| `M06_switch_tool` | `wrong_tool` | Extra old social source in v2 equivalent behavior | v2 kept old Twitter/social context after user switched source. | Added source-switch rule: latest turn overrides earlier source/tool context. |
| `G02_single_missing_news_topic` | `missing_info` | Empty/general web search in group iteration | "Tìm tin hôm nay" has no concrete topic, but the agent could still search too broadly. | Added explicit missing-news-topic example: call `ask_user`, never empty `search_web`. |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| `G01_single_top_social_anthropic` | Single-turn: tweets ABOUT a topic; "phổ biến nhất" maps to top results. | `search_social_posts(query="Anthropic", search_type="Top")` | PASS |
| `G02_single_missing_news_topic` | Single-turn: missing news topic should ask clarification, not guess. | `ask_user(response_type="text")` | PASS |
| `G03_single_confirm_send_with_text` | Single-turn: external posting requires confirmation even when content is provided. | `ask_user(response_type="yes_no")` | PASS |
| `G04_single_policy_source_citation` | Single-turn: internal policy question about viral tweet as fact source. | `search_policy(policy_area="source_citation")` | PASS |
| `G05_single_arxiv_latest_papers` | Single-turn: arXiv paper search with latest sort and explicit limit. | `search_papers(query="retrieval augmented generation", max_results=3, sort_by="submittedDate")` | PASS |
| `G06_multi_switch_to_url` | Multi-turn: later URL request overrides earlier web-search context. | `read_url(url="https://openai.com/blog/gpt-5")` | PASS |
| `G07_multi_limit_correction` | Multi-turn: keep account context and correct limit from 8 to 2. | `get_user_timeline(screenname="sama", limit=2)` | PASS |
| `G08_multi_carryover_news_topic` | Multi-turn: change query to robotics while carrying news/day context. | `search_web(query="robotics", topic="news", timeframe="day")` | PASS |
| `G09_multi_correct_person` | Multi-turn: later person correction overrides earlier person. | `get_user_timeline(screenname="karpathy", limit=3)` | PASS |
| `G10_multi_policy_before_publish` | Multi-turn: policy check before publishing must not send anything. | `search_policy(policy_area="external_publishing")` | PASS |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | `Theo company policy, tweet viral co duoc coi la nguon fact khong?` | `search_policy(policy_area="source_citation", query="tweet viral")` | `v3+pcf616643dbdb+t6632f96fa9b5` | Agent answered that viral tweets are Tier 3 signals, not confirmed facts without Tier 1/Tier 2 support. |
| 2 | `Tom tat 5 tweet moi nhat giup minh` | `ask_user(response_type="text")` | `v3+pcf616643dbdb+t6632f96fa9b5` | Agent asked which account to summarize instead of guessing. |
| 3 | `Dang ban tin nay len Telegram giup minh` | `ask_user(response_type="yes_no")` | `v3+pcf616643dbdb+t6632f96fa9b5` | Agent requested confirmation and did not call `send_message`. |
| 4 | `Demo tập trung vào vấn đề gì?` | `search_topic_notes(query=original demo/focus question)` | `v3-85f70c7ca84f` | Agent answered that the demo focuses on AI research intelligence: AI research, companies, agents, model releases, source quality, arXiv, social signals and safe external publishing. |
| 5 | `Theo policy công ty, đăng bản tin lên Telegram có cần xác nhận trước không?` | `search_policy(policy_area="external_publishing")` | `v3-e9f18473b0b7` | Agent answered that posting to Telegram requires explicit confirmation in the current conversation. |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | `transcripts/v3_openrouter_20260602T141048534791.transcript.json` | Telegram request routed to `ask_user(response_type="yes_no")` instead of `send_message`. | Prevents external posting before explicit confirmation. |
| arXiv/company policy | `runs/v3_B_group_openrouter_20260602T140810536234.json`; `company_policy/*.md` | Paper requests route to `search_papers`; policy requests route to `search_policy`. | Policy markdown is retrieved evidence, not executable instruction; arXiv is treated as early research. |
| UI | `ui_streamlit.py`; `transcripts/ui_v3_*.transcript.json`; public Cloudflare URL above | Streamlit chatbot uses the same prompt/tool registry and provides chat log + transcript download. | Cloudflare quick tunnel is temporary and only works while local Streamlit + `cloudflared` are running. |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
  - High-level behavior: AI research focus, do not guess, missing-info rules, source-switch rules, out-of-scope boundary, and confirmation-before-send rule.
- Which fixes belonged in `tools.yaml`?
  - Tool descriptions, argument guidance, policy-area mapping, verb-first tool names, and the instruction to pass the original demo/focus question into `search_topic_notes`.
- Which failure needed manual review instead of automatic grading?
  - Empty or over-broad searches such as `G02_single_missing_news_topic`, because automatic grading can check the tool call but humans need to verify whether the assistant avoided guessing.
- What would you improve next?
  - Add more policy documents and regression cases for external publishing, deploy with a stable named Cloudflare Tunnel, and add UI tests for common demo questions.
