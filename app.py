import email
from email.header import decode_header
import imaplib
from openai import OpenAI
import streamlit as st

# ============================================================
# 基本設定（初期値）
# ============================================================
DEFAULT_EMAIL = "gorigorired4649@gmail.com"
DEFAULT_PASSWORD = "scwt ixbk azww gczw"
LM_STUDIO_URL = "http://localhost:1234/v1"

# ページ全体のデザイン設定
st.set_page_config(
    page_title="ローカルAI メール要約ダッシュボード",
    page_icon="📬",
    layout="wide",
)

# タイトル
st.title("📬 ローカルAI メール要約アシスタント")
st.caption(
    "Gmailの未読メールをPC内のローカルLLM（LM Studio）で安全に読み込み・要約します。"
)

# サイドバー（設定画面）
with st.sidebar:
    st.header("⚙️ 設定")
    user_email = st.text_input("Gmailアドレス", value=DEFAULT_EMAIL)
    user_pwd = st.text_input(
        "アプリパスワード", value=DEFAULT_PASSWORD, type="password"
    )
    fetch_count = st.slider("取得する件数", min_value=1, max_value=10, value=3)
    lm_url = st.text_input("LM Studio URL", value=LM_STUDIO_URL)

    st.markdown("---")
    st.markdown(
        "🔒 **プライバシー保護**: データはすべてお使いのPC内で処理されます。"
    )


# メール補助関数
def decode_str(header_value):
    if not header_value:
        return ""
    decoded_fragments = decode_header(header_value)
    text = ""
    for fragment, encoding in decoded_fragments:
        if isinstance(fragment, bytes):
            text += fragment.decode(encoding or "utf-8", errors="ignore")
        else:
            text += str(fragment)
    return text


def get_mail_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))
            if content_type == "text/plain" and "attachment" not in content_disposition:
                charset = part.get_content_charset() or "utf-8"
                body = part.get_payload(decode=True).decode(
                    charset, errors="ignore"
                )
                break
    else:
        charset = msg.get_content_charset() or "utf-8"
        body = msg.get_payload(decode=True).decode(charset, errors="ignore")
    return body


def summarize_mail(client, subject, sender, body):
    prompt = f"""以下のメールを読み、要約してください。

【件名】: {subject}
【差出人】: {sender}
【本文】:
{body[:2500]}

---
【指示】:
1. どのような内容かを箇条書きで分かりやすく簡潔にまとめてください。
2. 返信やタスク等の対応が必要そうかどうか（「要対応」または「不要」）と、その理由を明記してください。
"""
    response = client.chat.completions.create(
        model="local-model",
        messages=[
            {
                "role": "system",
                "content": "あなたは優秀なビジネスアシスタントです。日本語で簡潔に回答してください。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    return response.choices[0].message.content


# メイン画面の実行ボタン
if st.button("🚀 最新の未読メールを取得して要約する", type="primary"):
    if not user_email or not user_pwd:
        st.error("メールアドレスとアプリパスワードを設定してください。")
    else:
        client = OpenAI(base_url=lm_url, api_key="lm-studio")

        with st.spinner("Gmailにアクセス中..."):
            try:
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(user_email, user_pwd)
                mail.select("INBOX")

                # 未読メールを検索
                status, messages = mail.search(None, "UNSEEN")
                email_ids = messages[0].split()

                if not email_ids:
                    st.info("🎉 現在、未読メールはありません！")
                    mail.logout()
                else:
                    target_ids = email_ids[-fetch_count:]
                    st.success(
                        f"未読メール {len(email_ids)} 件中、最新の {len(target_ids)} 件を取得しました。"
                    )

                    progress_bar = st.progress(0)

                    for idx, e_id in enumerate(reversed(target_ids)):
                        status, msg_data = mail.fetch(e_id, "(RFC822)")
                        for response_part in msg_data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                subject = decode_str(msg.get("Subject"))
                                sender = decode_str(msg.get("From"))
                                body = get_mail_body(msg)

                                # カード形式でUIを表示
                                with st.expander(
                                    f"📨 **{subject}** （差出人: {sender}）",
                                    expanded=True,
                                ):
                                    st.caption(f"送信元: {sender}")

                                    if not body.strip():
                                        st.warning(
                                            "本文が取得できませんでした（HTML専用メール等の可能性があります）。"
                                        )
                                    else:
                                        with st.spinner(
                                            f"「{subject[:15]}...」を要約中..."
                                        ):
                                            summary = summarize_mail(
                                                client, subject, sender, body
                                            )

                                        # 要約結果を枠で囲んで表示
                                        st.markdown(summary)

                        # プログレスバーを進める
                        progress_bar.progress((idx + 1) / len(target_ids))

                    mail.logout()
                    st.balloons()  # 要約完了時にちょっとしたアニメーション演出

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")