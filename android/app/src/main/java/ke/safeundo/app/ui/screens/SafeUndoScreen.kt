package ke.safeundo.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.KeyboardArrowRight
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ke.safeundo.app.data.CaseListItem
import ke.safeundo.app.data.TxSummary
import ke.safeundo.app.ui.SafeUndoViewModel
import ke.safeundo.app.ui.components.*
import ke.safeundo.app.ui.theme.Su
import kotlin.math.roundToInt

/** SafeUndo hub: report a mistake on a recent transaction, or track existing cases. */
@Composable
fun SafeUndoScreen(vm: SafeUndoViewModel, onBack: () -> Unit, onCase: (String) -> Unit) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    var picking by remember { mutableStateOf<TxSummary?>(null) }

    LaunchedEffect(Unit) { vm.reload() }

    SuScreen {
        SuTopBar("SafeUndo", onBack)
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            SimulatedBanner()
            ui.profile?.let {
                Text(
                    "Hi ${it.name.substringBefore(" ")}. You usually send ${kes(it.typicalAmount.p25.toDouble())}\u2013${kes(it.typicalAmount.p75.toDouble())}. " +
                        "SafeUndo warns you about unusual payments and helps you track reversal requests.",
                    color = Su.Muted, fontSize = 14.sp,
                )
            }

            SectionTitle("Made a mistake?")
            Text("Pick the transaction to report.", color = Su.Muted, fontSize = 14.sp)
            if (ui.recentTx.isEmpty()) Text("No recent transactions.", color = Su.Muted)
            ui.recentTx.forEach { tx ->
                TxRow(tx) {
                    if (tx.hasOpenCase) {
                        val open = ui.cases.firstOrNull { it.transaction.id == tx.id && it.status !in listOf("completed", "rejected") }
                        if (open != null) onCase(open.ref)
                    } else {
                        picking = tx
                    }
                }
            }

            SectionTitle("Your cases")
            if (ui.cases.isEmpty()) Text("No cases yet. When you report a mistake, you can track it here.", color = Su.Muted, fontSize = 14.sp)
            ui.cases.forEach { CaseCard(it) { onCase(it.ref) } }

            Text(
                "Reset demo data",
                color = Su.Muted, fontSize = 13.sp,
                modifier = Modifier.padding(vertical = 16.dp).clickable { vm.resetDemo() },
            )
        }
    }

    picking?.let { tx ->
        ReasonSheet(
            onDismiss = { picking = null },
            onSelect = { reason -> picking = null; vm.reportMistake(tx.id, reason, onCase) },
        )
    }
}

@Composable
private fun TxRow(tx: TxSummary, onClick: () -> Unit) {
    Row(
        Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Su.Card).clickable(onClick = onClick).padding(14.dp),
        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        NameAvatar(tx.recipientName ?: tx.txTypeLabel, tx.recipient, size = 44.dp, textSize = 16.sp)
        Column(Modifier.weight(1f)) {
            Text(tx.recipientName ?: tx.recipient, color = Su.Text, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            Text("${tx.txTypeLabel} \u00B7 ${fmtShort(tx.ts)}", color = Su.Muted, fontSize = 12.sp)
        }
        Column(horizontalAlignment = Alignment.End) {
            Text(kes(tx.amount), color = Su.Text, fontWeight = FontWeight.Bold)
            if (tx.hasOpenCase) OutlinedTag("Case open", Su.Amber)
        }
        Icon(Icons.AutoMirrored.Filled.KeyboardArrowRight, null, tint = Su.Muted)
    }
}

@Composable
private fun CaseCard(c: CaseListItem, onClick: () -> Unit) {
    SuCard(Modifier.clickable(onClick = onClick)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(c.ref, Modifier.weight(1f), color = Su.Text, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            Pill(c.statusLabel, statusColor(c.status).copy(alpha = 0.18f), statusColor(c.status))
        }
        Text("${c.reasonLabel} \u00B7 ${kes(c.transaction.amount)} \u00B7 ${c.transaction.txTypeLabel}", color = Su.Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp))
        c.prediction?.let { p ->
            Spacer(Modifier.height(10.dp))
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("Est. ${p.label}", color = Su.Text, fontSize = 14.sp, modifier = Modifier.weight(1f))
                Text("Delay risk ${(p.delayRisk * 100).roundToInt()}%", color = riskColor(p.riskLevel), fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
            }
        }
    }
}
