package ke.safeundo.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ke.safeundo.app.data.CaseDetail
import ke.safeundo.app.data.Prediction
import ke.safeundo.app.ui.SafeUndoViewModel
import ke.safeundo.app.ui.components.*
import ke.safeundo.app.ui.theme.Su
import kotlin.math.roundToInt

/** Case tracker: status timeline, predictive insights, guidance and a simulated-update control. */
@Composable
fun CaseScreen(vm: SafeUndoViewModel, ref: String, onBack: () -> Unit) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val c = ui.activeCase?.takeIf { it.ref == ref }

    LaunchedEffect(ref) { vm.loadCase(ref) }

    SuScreen {
        SuTopBar("Case $ref", onBack)
        if (c == null) {
            Box(Modifier.weight(1f).fillMaxWidth(), contentAlignment = Alignment.Center) { CircularProgressIndicator(color = Su.Green) }
            return@SuScreen
        }
        val closed = c.status == "completed" || c.status == "rejected"
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(14.dp)) {
            SimulatedBanner("Simulated case. Status updates and estimates are demonstration data.")
            HeaderCard(c)
            when {
                c.prediction != null -> PredictionCard(c.prediction)
                c.status == "completed" -> OutcomeCard("Reversal completed", "Check your M-PESA SMS and balance. (Simulated outcome)", Su.Green)
                c.status == "rejected" -> OutcomeCard("Request rejected", c.rejectionReason ?: "No reason available.", Su.Red)
            }
            TimelineCard(c)
            GuidanceCard(c)
            SuCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Demo control", Modifier.weight(1f), color = Su.Text, fontWeight = FontWeight.SemiBold)
                    Pill("SIMULATED", Su.Amber.copy(alpha = 0.18f), Su.Amber)
                }
                Text("Moves the case to its next status and fast-forwards the demo clock by 4 hours. Watch the estimate change.", color = Su.Muted, fontSize = 13.sp, modifier = Modifier.padding(vertical = 10.dp))
                PrimaryButton("Simulate next update", { vm.advance(c.ref) }, enabled = !closed, loading = busy)
            }
            Text(c.disclaimer, color = Su.Muted, fontSize = 12.sp, modifier = Modifier.padding(bottom = 24.dp))
        }
    }
}

@Composable
private fun HeaderCard(c: CaseDetail) {
    SuCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(c.ref, Modifier.weight(1f), color = Su.Text, fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Pill(c.statusLabel, statusColor(c.status).copy(alpha = 0.18f), statusColor(c.status))
        }
        Text("${c.reasonLabel} \u00B7 ${kes(c.transaction.amount)}", color = Su.Text, fontSize = 16.sp, modifier = Modifier.padding(top = 6.dp))
        Text(
            "${c.transaction.txTypeLabel} to ${c.transaction.recipientName ?: c.transaction.recipient} \u00B7 ${c.transaction.mpesaRef}",
            color = Su.Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp),
        )
    }
}

@Composable
private fun PredictionCard(p: Prediction) {
    val col = riskColor(p.riskLevel)
    var open by remember { mutableStateOf(false) }
    SuCard {
        Text("Estimated remaining time", color = Su.Muted, fontSize = 14.sp)
        Text(p.label, color = Su.Text, fontSize = 34.sp, fontWeight = FontWeight.Bold)
        Text("Open for ${"%.1f".format(p.elapsedHours)} hours", color = Su.Muted, fontSize = 12.sp)
        Spacer(Modifier.height(16.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text("Predicted delay risk", Modifier.weight(1f), color = Su.Muted, fontSize = 14.sp)
            Pill("${p.riskLevel} risk", col.copy(alpha = 0.18f), col)
        }
        Text("${(p.delayRisk * 100).roundToInt()}%", color = col, fontSize = 30.sp, fontWeight = FontWeight.Bold)
        LinearProgressIndicator(
            progress = { p.delayRisk.toFloat().coerceIn(0f, 1f) }, color = col, trackColor = Su.Raised,
            modifier = Modifier.fillMaxWidth().height(8.dp).clip(RoundedCornerShape(4.dp)),
        )
        HorizontalDivider(Modifier.padding(vertical = 14.dp), color = Su.Outline)
        Text("Suggested action", color = Su.Muted, fontSize = 14.sp)
        Text(p.action, color = Su.Text, fontSize = 16.sp, modifier = Modifier.padding(top = 4.dp))
        Text(
            if (open) "Hide why \u25B4" else "Why is this case flagged? \u25BE",
            color = Su.Green, fontSize = 14.sp, fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(top = 12.dp).clickable { open = !open },
        )
        if (open) p.why.forEach { Text("\u2022 $it", color = Su.Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 6.dp)) }
        Text("Illustrative values from a model trained on synthetic data. Not live Safaricom case data.", color = Su.Muted, fontSize = 11.sp, modifier = Modifier.padding(top = 12.dp))
    }
}

@Composable
private fun OutcomeCard(title: String, body: String, col: Color) {
    SuCard {
        Text(title, color = col, fontSize = 20.sp, fontWeight = FontWeight.Bold)
        Text(body, color = Su.Text, fontSize = 15.sp, modifier = Modifier.padding(top = 6.dp))
    }
}

@Composable
private fun TimelineCard(c: CaseDetail) {
    SuCard {
        Text("Status timeline", color = Su.Text, fontWeight = FontWeight.SemiBold, fontSize = 16.sp, modifier = Modifier.padding(bottom = 12.dp))
        c.timeline.forEachIndexed { i, s ->
            val at = c.history.firstOrNull { it.status == s.status }?.ts
            val col = if (s.reached) statusColor(s.status) else Su.Outline
            Row(Modifier.height(IntrinsicSize.Min)) {
                Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.width(28.dp)) {
                    Box(
                        Modifier.size(14.dp).clip(CircleShape).background(if (s.reached) col else Color.Transparent)
                            .border(2.dp, col, CircleShape),
                    )
                    if (i < c.timeline.lastIndex) Box(Modifier.width(2.dp).weight(1f).background(Su.Outline))
                }
                Column(Modifier.padding(bottom = 18.dp)) {
                    Text(s.label, color = if (s.reached) Su.Text else Su.Muted, fontWeight = if (s.reached) FontWeight.SemiBold else FontWeight.Normal)
                    Text(if (at != null) fmtShort(at) + " (simulated)" else "Pending", color = Su.Muted, fontSize = 12.sp)
                }
            }
        }
    }
}

@Composable
private fun GuidanceCard(c: CaseDetail) {
    val g = c.guidance
    SuCard {
        Text(g.title, color = Su.Text, fontWeight = FontWeight.SemiBold, fontSize = 16.sp)
        g.steps.forEachIndexed { i, s ->
            Row(Modifier.padding(top = 10.dp), horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Text("${i + 1}.", color = Su.Green, fontWeight = FontWeight.Bold)
                Text(s, color = Su.Text, fontSize = 15.sp)
            }
        }
        if (!g.verifiedProcedure) {
            Spacer(Modifier.height(10.dp))
            OutlinedTag("Verify the official procedure", Su.Amber)
        }
        Text(g.note, color = Su.Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 10.dp))
        Text(g.disclaimer, color = Su.Muted, fontSize = 12.sp, modifier = Modifier.padding(top = 4.dp))
    }
}
