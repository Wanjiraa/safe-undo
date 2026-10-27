package ke.safeundo.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Close
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ke.safeundo.app.ui.SafeUndoViewModel
import ke.safeundo.app.ui.components.*
import ke.safeundo.app.ui.theme.Su

private fun confirmTitle(txType: String) = when (txType) {
    "send_money" -> "Send money to mobile number"
    "pochi" -> "Send to Pochi la Biashara"
    "paybill" -> "Pay to Paybill"
    else -> "Pay to till number"
}

/** Mirrors My OneApp's "Confirm" screen. */
@Composable
fun ConfirmScreen(vm: SafeUndoViewModel, onBack: () -> Unit, onDone: () -> Unit) {
    val d by vm.draft.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val who = d.recipientName ?: d.recipient

    SuScreen {
        SuTopBar("Confirm", onBack)
        Box(Modifier.weight(1f).fillMaxWidth().padding(horizontal = 16.dp), contentAlignment = Alignment.Center) {
            Box(Modifier.fillMaxWidth()) {
                Column(
                    Modifier.padding(top = 50.dp).fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Su.Card)
                        .border(1.dp, Su.Outline, RoundedCornerShape(24.dp)),
                ) {
                    Text(confirmTitle(d.txType), Modifier.fillMaxWidth().padding(top = 66.dp, bottom = 22.dp), color = Su.Text, fontSize = 22.sp, textAlign = TextAlign.Center)
                    HorizontalDivider(color = Su.Outline)
                    Column(Modifier.padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
                        ConfirmRow("Send to", who)
                        HorizontalDivider(color = Su.Outline)
                        ConfirmRow("Amount", ksh2(d.amount))
                        HorizontalDivider(color = Su.Outline)
                        ConfirmRow("Transaction cost", "N/A")
                    }
                }
                Box(Modifier.align(Alignment.TopCenter).size(100.dp).clip(CircleShape).background(Su.Raised).border(2.dp, Su.Outline, CircleShape), contentAlignment = Alignment.Center) {
                    NameAvatar(d.recipientName ?: "?", d.recipient, size = 56.dp, textSize = 22.sp)
                }
            }
        }
        PrimaryButton("Send", { vm.send(onDone) }, Modifier.padding(16.dp), loading = busy)
    }
}

@Composable
private fun ConfirmRow(label: String, value: String) {
    Column {
        Text(label, color = Su.Muted, fontSize = 16.sp)
        Text(value, color = Su.Text, fontSize = 24.sp, fontWeight = FontWeight.Bold)
    }
}

/** Mirrors My OneApp's success screen, including "Reverse transaction", which opens SafeUndo. */
@Composable
fun SuccessScreen(vm: SafeUndoViewModel, onClose: () -> Unit, onCase: (String) -> Unit) {
    val tx by vm.lastTx.collectAsStateWithLifecycle()
    val ctx = LocalContext.current
    val clipboard = LocalClipboardManager.current
    var showReasons by remember { mutableStateOf(false) }
    val t = tx ?: run { SuScreen { SuTopBar("Receipt", onClose) }; return }
    val toast = { m: String -> Toast.makeText(ctx, m, Toast.LENGTH_SHORT).show() }

    SuScreen {
        Row(Modifier.fillMaxWidth().padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            IconCircle(Icons.Filled.Close, "Close", onClose, tint = Su.Red)
            Spacer(Modifier.weight(1f))
            Row(
                Modifier.clip(RoundedCornerShape(16.dp)).background(Su.Card).clickable { toast("Share is not part of the demo") }.padding(horizontal = 18.dp, vertical = 16.dp),
                verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(10.dp),
            ) {
                Icon(Icons.Outlined.Share, null, tint = Su.Green)
                Text("Share Details", color = Su.Text, fontSize = 17.sp, fontWeight = FontWeight.Medium)
            }
        }
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Box(Modifier.fillMaxWidth()) {
                Column(
                    Modifier.padding(top = 50.dp).fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Su.Card).border(1.dp, Su.Outline, RoundedCornerShape(24.dp)).padding(20.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                ) {
                    Spacer(Modifier.height(56.dp))
                    Text("Your transaction was successful", color = Su.Text, fontSize = 30.sp, textAlign = TextAlign.Center, lineHeight = 36.sp)
                    Text(fmtLong(t.ts), color = Su.Muted, fontSize = 15.sp, modifier = Modifier.padding(top = 14.dp))
                    Text(ksh2(t.amount), color = Su.Text, fontSize = 38.sp, fontWeight = FontWeight.Bold, modifier = Modifier.padding(top = 18.dp))
                    Row(Modifier.padding(top = 10.dp)) {
                        Text("Transaction cost:", color = Su.Muted, fontSize = 15.sp)
                        Text(ksh2(t.transactionCost), color = Su.Text, fontSize = 15.sp, fontWeight = FontWeight.Bold)
                    }
                    Row(
                        Modifier.padding(top = 10.dp).clickable { clipboard.setText(AnnotatedString(t.mpesaRef)); toast("Copied") },
                        verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp),
                    ) {
                        Text("ID: ${t.mpesaRef}", color = Su.Green, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                        Icon(Icons.Outlined.ContentCopy, "Copy ID", tint = Su.Green, modifier = Modifier.size(18.dp))
                        Text("Copy", color = Su.Green, fontSize = 18.sp)
                    }
                    Column(Modifier.padding(top = 20.dp).fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Su.Raised).padding(18.dp)) {
                        Text("Send to:", color = Su.Text, fontSize = 15.sp)
                        Row(Modifier.padding(top = 10.dp), verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                            NameAvatar(t.recipientName ?: "?", t.recipient, size = 56.dp)
                            Column {
                                Text(t.recipientName ?: t.txTypeLabel, color = Su.Text, fontSize = 17.sp)
                                Text(t.recipient, color = Su.Text, fontSize = 17.sp)
                            }
                        }
                    }
                }
                Box(Modifier.align(Alignment.TopCenter).size(100.dp).clip(CircleShape).background(Su.Raised).border(2.dp, Su.Outline, CircleShape), contentAlignment = Alignment.Center) {
                    Text("\uD83C\uDF89", fontSize = 44.sp)
                }
            }
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                ResultAction("Add to favourites", Icons.Outlined.StarBorder) { toast("Not part of the demo") }
                ResultAction("Reverse transaction", Icons.Outlined.Replay, highlight = true) { showReasons = true }
                ResultAction("Schedule payment", Icons.Outlined.EditCalendar) { toast("Not part of the demo") }
                ResultAction("Download receipt", Icons.Outlined.Receipt) { toast("Not part of the demo") }
            }
            Spacer(Modifier.height(16.dp))
        }
    }

    if (showReasons) {
        ReasonSheet(
            onDismiss = { showReasons = false },
            onSelect = { reason -> showReasons = false; vm.reportMistake(t.id, reason, onCase) },
        )
    }
}

@Composable
private fun RowScope.ResultAction(label: String, icon: ImageVector, highlight: Boolean = false, onClick: () -> Unit) {
    Column(Modifier.weight(1f).clickable(onClick = onClick), horizontalAlignment = Alignment.CenterHorizontally) {
        Box(Modifier.size(62.dp).clip(CircleShape).background(Su.Raised), contentAlignment = Alignment.Center) {
            Icon(icon, label, tint = if (highlight) Su.Amber else Su.Green, modifier = Modifier.size(28.dp))
        }
        Text(label, color = Su.Text, fontSize = 13.sp, textAlign = TextAlign.Center, modifier = Modifier.padding(top = 6.dp))
    }
}
