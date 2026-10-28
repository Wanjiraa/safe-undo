package ke.safeundo.app.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ke.safeundo.app.data.DemoContacts
import ke.safeundo.app.ui.Draft
import ke.safeundo.app.ui.SafeUndoViewModel
import ke.safeundo.app.ui.components.*
import ke.safeundo.app.ui.theme.Su

data class PayTab(val txType: String, val label: String, val numberLabel: String, val hasAccount: Boolean = false)

val SEND_TABS = listOf(
    PayTab("send_money", "Mobile number", "Enter Phone Number"),
    PayTab("pochi", "Pochi la Biashara", "Enter Pochi Number"),
)
val LIPA_TABS = listOf(
    PayTab("buy_goods", "Buy Goods", "Enter till number"),
    PayTab("paybill", "Paybill", "Enter business number", hasAccount = true),
    PayTab("pochi", "Pochi la Bi\u2026", "Enter Pochi Number"),
)

/** Shared form behind both "Send Money" and "Lipa na M-PESA", mirroring My OneApp. */
@Composable
fun PayScreen(vm: SafeUndoViewModel, title: String, tabs: List<PayTab>, onBack: () -> Unit, onContinue: () -> Unit) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    val warning by vm.warning.collectAsStateWithLifecycle()
    val lookupName by vm.lookupName.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()

    var tab by remember { mutableIntStateOf(0) }
    var number by remember { mutableStateOf("") }
    var account by remember { mutableStateOf("") }
    var amountText by remember { mutableStateOf("") }

    val t = tabs[tab]
    val isPhone = t.txType == "send_money" || t.txType == "pochi"
    val phone = normalizedPhone(number)
    val digits = number.filter { it.isDigit() }
    val validNumber = if (isPhone) phone != null else digits.length in 5..7
    val amount = amountText.toDoubleOrNull() ?: 0.0
    val balance = ui.profile?.balance
    val overBalance = balance != null && amount > balance
    val canContinue = validNumber && amount > 0 && !overBalance && (!t.hasAccount || account.isNotBlank())

    LaunchedEffect(number, tab) {
        val target = if (isPhone) phone else digits.takeIf { it.length in 5..7 }
        if (target != null) vm.lookupRecipient(t.txType, target) else vm.clearLookup()
    }

    SuScreen {
        SuTopBar(title, onBack)
        Column(
            Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            SegmentedTabs(tabs.map { it.label }, tab, { tab = it; number = ""; account = "" })

            if (isPhone) {
                Text("Favourites", color = Su.Text, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(18.dp)) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(Modifier.size(52.dp).clip(CircleShape).background(Su.Raised), contentAlignment = Alignment.Center) {
                            Icon(Icons.Filled.Add, "Add favourite", tint = Su.Red)
                        }
                        Text("Add", color = Su.Muted, fontSize = 13.sp, modifier = Modifier.padding(top = 4.dp))
                    }
                    DemoContacts.forCustomer(ui.customerId).forEach { (name, num) ->
                        Column(Modifier.width(72.dp).clickable { number = num }, horizontalAlignment = Alignment.CenterHorizontally) {
                            NameAvatar(name, name, size = 52.dp, textSize = 18.sp)
                            Text(name, color = Su.Muted, fontSize = 13.sp, maxLines = 2, modifier = Modifier.padding(top = 4.dp))
                        }
                    }
                }
            } else if (t.txType == "buy_goods") {
                Text("Popular Tills (Buy Goods)", color = Su.Text, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DemoContacts.buyGoodsTills.forEach { (merchant, till) ->
                        Column(
                            Modifier.weight(1f).clip(RoundedCornerShape(12.dp)).background(Su.Card)
                                .border(1.dp, if (number == till) Su.Green else Su.Outline, RoundedCornerShape(12.dp))
                                .clickable { number = till }.padding(10.dp),
                        ) {
                            Text(till, color = Su.Green, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                            Text(merchant, color = Su.Muted, fontSize = 11.sp, maxLines = 1)
                        }
                    }
                }
            } else if (t.txType == "paybill") {
                Text("Popular PayBills", color = Su.Text, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DemoContacts.paybills.forEach { pb ->
                        Column(
                            Modifier.weight(1f).clip(RoundedCornerShape(12.dp)).background(Su.Card)
                                .border(1.dp, if (number == pb.businessNumber) Su.Green else Su.Outline, RoundedCornerShape(12.dp))
                                .clickable { number = pb.businessNumber; account = pb.sampleAccount }.padding(10.dp),
                        ) {
                            Text(pb.businessNumber, color = Su.Green, fontSize = 14.sp, fontWeight = FontWeight.Bold)
                            Text(pb.name, color = Su.Muted, fontSize = 11.sp, maxLines = 1)
                        }
                    }
                }
            }

            SuField(
                label = t.numberLabel, value = number, onChange = { number = it.take(13) }, placeholder = t.numberLabel,
                keyboard = KeyboardType.Phone,
                trailing = { Icon(if (isPhone) Icons.Outlined.Person else Icons.Outlined.QrCodeScanner, null, tint = Su.Green, modifier = Modifier.padding(end = 8.dp)) },
                helper = if (validNumber) lookupName else null,
            )
            if (isPhone) {
                val sampleList = if (t.txType == "pochi") DemoContacts.pochiChips else DemoContacts.demoPhoneChips
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    sampleList.forEach { (num, tag) ->
                        Column(
                            Modifier.weight(1f).clip(RoundedCornerShape(10.dp)).background(Su.Card)
                                .border(1.dp, if (number == num) Su.Green else Su.Outline, RoundedCornerShape(10.dp))
                                .clickable { number = num }.padding(horizontal = 8.dp, vertical = 6.dp),
                        ) {
                            Text(num, color = Su.Green, fontSize = 12.sp, fontWeight = FontWeight.Bold, maxLines = 1)
                            Text(tag, color = Su.Muted, fontSize = 10.sp, maxLines = 1)
                        }
                    }
                }
            }
            if (t.hasAccount) {
                SuField("Enter account number", account, { account = it.take(20) }, "Account number", keyboard = KeyboardType.Text)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    DemoContacts.paybillAccounts.forEach { acc ->
                        Text(
                            acc, color = if (account == acc) Su.Text else Su.Muted, fontSize = 12.sp,
                            modifier = Modifier.clip(RoundedCornerShape(50))
                                .background(if (account == acc) Su.Green else Su.Raised)
                                .clickable { account = acc }.padding(horizontal = 12.dp, vertical = 6.dp),
                        )
                    }
                }
            }
            SuField(
                label = "Enter Amount", value = amountText,
                onChange = { s -> if (s.count { it == '.' } <= 1 && s.all { it.isDigit() || it == '.' }) amountText = s.take(9) },
                placeholder = "0", suffix = "Ksh",
                helper = when {
                    overBalance -> "Amount is more than your M-PESA balance"
                    balance != null -> "Balance: ${ksh2(balance)}"
                    else -> null
                },
                helperColor = if (overBalance) Su.Red else Su.Muted,
            )
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("800" to "Usual (KSh 800)", "5000" to "KSh 5,000", "20000" to "Unusual (KSh 20,000)").forEach { (amt, label) ->
                    Text(
                        label, color = if (amountText == amt) Su.Text else Su.Muted, fontSize = 12.sp,
                        modifier = Modifier.clip(RoundedCornerShape(50))
                            .background(if (amountText == amt) Su.Green else Su.Raised)
                            .clickable { amountText = amt }.padding(horizontal = 12.dp, vertical = 6.dp),
                    )
                }
            }

            Text("Select Payment Method", color = Su.Text, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Row(horizontalArrangement = Arrangement.spacedBy(14.dp)) {
                PayMethod("M-PESA", balance?.let { "Bal. ${ksh2(it).replace(".00", "")}" } ?: "\u2026", selected = true, modifier = Modifier.weight(1f))
                PayMethod("Shiriki Pay", "Select", selected = false, modifier = Modifier.weight(1f))
            }

            PrimaryButton("Continue", enabled = canContinue, loading = busy, onClick = {
                vm.prepare(Draft(t.txType, phone ?: digits, null, amount, account), onContinue)
            })

            Text("Do More", color = Su.Text, fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                listOf("Send to Many" to Icons.Outlined.Groups, "Request Money" to Icons.Outlined.RequestQuote, "Invest to ZiiDi" to Icons.Outlined.TrendingUp).forEach { (l, ic) ->
                    Column(
                        Modifier.weight(1f).clip(RoundedCornerShape(20.dp)).background(Su.Card).padding(vertical = 20.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                    ) {
                        Icon(ic, l, tint = Su.Green, modifier = Modifier.size(30.dp))
                        Text(l, color = Su.Text, fontSize = 14.sp, modifier = Modifier.padding(top = 8.dp, start = 6.dp, end = 6.dp), maxLines = 2)
                    }
                }
            }
            Spacer(Modifier.height(24.dp))
        }
    }

    warning?.let {
        SafeUndoWarningSheet(it, onContinue = { vm.dismissWarning(); onContinue() }, onCancel = vm::dismissWarning)
    }
}

@Composable
private fun PayMethod(name: String, sub: String, selected: Boolean, modifier: Modifier) {
    Box(
        modifier.clip(RoundedCornerShape(16.dp)).background(Su.Card)
            .border(2.dp, if (selected) Su.Green else Su.Outline, RoundedCornerShape(16.dp)).padding(16.dp),
    ) {
        Column {
            Text(name, color = Su.Text, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
            Text(sub, color = Su.Muted, fontSize = 16.sp)
        }
        if (selected) Icon(Icons.Outlined.CheckCircle, "Selected", tint = Su.Green, modifier = Modifier.align(Alignment.TopEnd).size(20.dp))
    }
}
