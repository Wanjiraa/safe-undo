# Demo script (about 4 minutes)

Start the backend, open `http://localhost:8000/` (USSD) and the Android app side by side.

1. **Prevent (USSD).** Customer Amina. Dial `*334#` > 1 > `0700123401` (known) > `800`: no warning.
   Repeat with `0799999999` and `20000`: the *Unusual transaction detected* screen appears with reasons. Reply 1 to continue.
2. **Prevent (Android).** Quick Actions > Send Money > same inputs. SafeUndo bottom sheet appears. Continue.
3. **Recover.** On the success screen tap *Reverse transaction*, choose *Wrong amount*. A tracked case `SU-10xx` opens
   with Send Money guidance (forward the SMS to 456) and a prediction.
4. **Same case on the other channel.** In USSD: `*334#` > 3 > 2 shows the same case, status and estimate.
5. **Predict.** Open `SU-1044` (Brian, Buy Goods refund): elevated delay risk, overdue, follow-up advice.
   Open `SU-1042` (Amina): low risk. Tap *Simulate next update* and watch the estimate move.
6. **Be honest.** Show `/api/ml/metrics` and the SIMULATED labels. State what is working vs simulated.

Reset anytime with the *Reset demo data* control.
