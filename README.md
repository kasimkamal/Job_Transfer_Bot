# Job_Transfer_Bot

register the webhook manually
If url is empty or wrong, set it explicitly:

bash
curl -s -F "url=https://job-transfer-bot.onrender.com/<YOUR_TOKEN>" "https://api.telegram.org/bot<YOUR_TOKEN>/setWebhook"
Expect {"ok":true,...}. After that, check getWebhookInfo again.
