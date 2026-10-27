package ke.safeundo.app.ui.screens

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.Send
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import ke.safeundo.app.ui.SafeUndoViewModel
import ke.safeundo.app.ui.components.*
import ke.safeundo.app.ui.theme.Su

private data class Tile(val label: String, val icon: ImageVector, val isNew: Boolean = false, val action: () -> Unit)

/** Replica of the My OneApp "Quick Actions" screen with SafeUndo added as a simulated entry point. */
@Composable
fun HomeScreen(vm: SafeUndoViewModel, onSend: () -> Unit, onLipa: () -> Unit, onSafeUndo: () -> Unit) {
    val ui by vm.ui.collectAsStateWithLifecycle()
    val ctx = LocalContext.current
    val soon = { Toast.makeText(ctx, "Not part of the SafeUndo demo", Toast.LENGTH_SHORT).show() }

    val quick = listOf(
        Tile("Send Money", Icons.AutoMirrored.Outlined.Send, action = onSend),
        Tile("Lipa na M-PESA", Icons.Outlined.ShoppingCart, action = onLipa),
        Tile("Withdraw Money", Icons.Outlined.Payments, action = soon),
        Tile("SafeUndo", Icons.Outlined.Shield, isNew = true, action = onSafeUndo),
        Tile("Buy Bundles", Icons.Outlined.Wifi, action = soon),
        Tile("Airtime Top Up", Icons.Outlined.Call, action = soon),
        Tile("Tunukiwa Bundles", Icons.Outlined.CardGiftcard, action = soon),
        Tile("Home Internet", Icons.Outlined.Router, action = soon),
    )
    val transact = listOf(
        Tile("Send Money", Icons.AutoMirrored.Outlined.Send, action = onSend),
        Tile("Lipa na M-PESA", Icons.Outlined.ShoppingCart, action = onLipa),
        Tile("Withdraw Money", Icons.Outlined.Payments, action = soon),
        Tile("SafeUndo", Icons.Outlined.Shield, isNew = true, action = onSafeUndo),
        Tile("International Transfer", Icons.Outlined.Public, action = soon),
        Tile("Pochi Wallet", Icons.Outlined.AccountBalanceWallet, action = soon),
        Tile("Bill Manager", Icons.Outlined.ReceiptLong, action = soon),
        Tile("Cost Calculator", Icons.Outlined.Calculate, action = soon),
    )

    SuScreen {
        // Demo bar: makes it obvious this is a simulation and lets judges switch customer profiles.
        Row(
            Modifier.fillMaxWidth().background(Su.GreenSoft).padding(horizontal = 16.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("Simulated My OneApp", color = Su.Green, fontSize = 12.sp, fontWeight = FontWeight.Bold, modifier = Modifier.weight(1f))
            val name = ui.profile?.name ?: "Loading\u2026"
            Text(
                "$name \u25BE", color = Su.Text, fontSize = 12.sp,
                modifier = Modifier.clickable {
                    val list = ui.customers
                    if (list.isNotEmpty()) {
                        val i = list.indexOfFirst { it.id == ui.customerId }
                        vm.selectCustomer(list[(i + 1) % list.size].id)
                    }
                }.padding(4.dp),
            )
        }
        SuTopBar("Quick Actions", null)
        Column(Modifier.weight(1f).verticalScroll(rememberScrollState()).padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Row(
                Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Su.Bg)
                    .padding(vertical = 18.dp, horizontal = 18.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Icon(Icons.Outlined.Search, null, tint = Su.Green)
                Spacer(Modifier.width(12.dp))
                Text("Search", color = Su.Muted, fontSize = 18.sp)
            }
            SuCard {
                Row(Modifier.fillMaxWidth()) {
                    Text("Quick Actions", Modifier.weight(1f), color = Su.Green, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                    Text("Edit", color = Su.Green, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                }
                Spacer(Modifier.height(12.dp))
                TileGrid(quick)
            }
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                listOf("All", "Transact", "Bundles", "Airtime").forEachIndexed { i, l ->
                    Text(
                        l, color = Su.Text, fontSize = 15.sp,
                        modifier = Modifier.clip(RoundedCornerShape(50)).background(if (i == 0) Su.Green else Su.Raised)
                            .padding(horizontal = 18.dp, vertical = 12.dp),
                    )
                }
            }
            SectionTitle("Transact")
            TileGrid(transact)
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun TileGrid(tiles: List<Tile>) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        tiles.chunked(4).forEach { row ->
            Row(Modifier.fillMaxWidth()) {
                row.forEach { ActionTile(it, Modifier.weight(1f)) }
                repeat(4 - row.size) { Spacer(Modifier.weight(1f)) }
            }
        }
    }
}

@Composable
private fun ActionTile(t: Tile, modifier: Modifier) {
    Column(
        modifier.clip(RoundedCornerShape(16.dp)).clickable(onClick = t.action).padding(vertical = 6.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Box(Modifier.size(62.dp).clip(CircleShape).background(Su.Raised), contentAlignment = Alignment.Center) {
            Icon(t.icon, t.label, tint = if (t.isNew) Su.Amber else Su.Green, modifier = Modifier.size(28.dp))
        }
        Spacer(Modifier.height(6.dp))
        Text(t.label, color = Su.Text, fontSize = 13.sp, textAlign = TextAlign.Center, maxLines = 2, minLines = 2)
    }
}
