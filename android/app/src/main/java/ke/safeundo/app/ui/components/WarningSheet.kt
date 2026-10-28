package ke.safeundo.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Warning
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ke.safeundo.app.data.ScoreResult
import ke.safeundo.app.ui.theme.Su
import kotlin.math.roundToInt

/** The pre-send confirmation moment. SafeUndo warns; it never blocks a transaction. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SafeUndoWarningSheet(result: ScoreResult, onContinue: () -> Unit, onCancel: () -> Unit) {
    val w = result.warning ?: return
    ModalBottomSheet(
        onDismissRequest = onCancel, sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = Su.Bg, contentColor = Su.Text,
    ) {
        Column(
            Modifier.padding(horizontal = 20.dp).padding(bottom = 24.dp).navigationBarsPadding(),
            horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            val recipientDisplay = w.recipientName ?: result.recipientName ?: w.recipient
            Box(Modifier.size(64.dp).clip(CircleShape).background(Su.Raised), contentAlignment = Alignment.Center) {
                Icon(Icons.Outlined.Warning, "Warning", tint = Su.Amber, modifier = Modifier.size(32.dp))
            }
            Text(w.title, fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Su.Text, textAlign = TextAlign.Center)
            Text("${kes(w.amount)} to $recipientDisplay", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = Su.Amber, textAlign = TextAlign.Center)
            SuCard {
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text("Amount", color = Su.Muted, modifier = Modifier.weight(1f))
                    Text(kes(w.amount), color = Su.Text, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }
                Spacer(Modifier.height(10.dp))
                Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                    Text("Sending to", color = Su.Muted, modifier = Modifier.weight(1f))
                    Text(recipientDisplay, color = Su.Text, fontWeight = FontWeight.SemiBold)
                }
            }
            Column(Modifier.fillMaxWidth(), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                result.reasons.forEach { Text("\u2022 $it", color = Su.Text, fontSize = 15.sp) }
            }
            Text("Unusualness score ${result.riskScore.roundToInt()}/100", color = Su.Muted, fontSize = 12.sp)
            PrimaryButton("Yes, continue", onContinue)
            SecondaryButton("Cancel", onCancel)
            Text(
                "SafeUndo adds a moment to double-check. It never blocks a legitimate transaction.",
                color = Su.Muted, fontSize = 12.sp, textAlign = TextAlign.Center,
            )
        }
    }
}
