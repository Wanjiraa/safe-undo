package ke.safeundo.app.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import ke.safeundo.app.ui.theme.Su

val REVERSAL_REASONS = listOf(
    "wrong_number" to "Wrong number", "wrong_amount" to "Wrong amount", "fraud" to "Fraud",
    "refund" to "Refund", "other" to "Other Reason",
)

/** "Reverse transaction" sheet, same reasons as My OneApp. Choosing one opens a tracked SafeUndo case. */
@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ReasonSheet(onSelect: (String) -> Unit, onDismiss: () -> Unit) {
    ModalBottomSheet(
        onDismissRequest = onDismiss, sheetState = rememberModalBottomSheetState(skipPartiallyExpanded = true),
        containerColor = Su.Bg, contentColor = Su.Text,
    ) {
        Column(Modifier.padding(horizontal = 16.dp).padding(bottom = 24.dp).navigationBarsPadding(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
            Text("Reverse transaction", Modifier.fillMaxWidth(), textAlign = TextAlign.Center, fontSize = 20.sp, color = Su.Text)
            Spacer(Modifier.height(8.dp))
            Text("Choose a reason for reversal", Modifier.fillMaxWidth(), textAlign = TextAlign.Center, fontSize = 20.sp, color = Su.Text)
            Spacer(Modifier.height(8.dp))
            REVERSAL_REASONS.forEach { (id, label) ->
                Row(
                    Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Su.Card)
                        .clickable { onSelect(id) }.padding(horizontal = 18.dp, vertical = 20.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Text(label, Modifier.weight(1f), color = Su.Text, fontSize = 17.sp)
                    androidx.compose.material3.Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, null, tint = Su.Muted)
                }
            }
            Text(
                "SafeUndo will show the right steps for this payment type and track the request. It cannot reverse a transaction itself.",
                color = Su.Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp),
            )
        }
    }
}
