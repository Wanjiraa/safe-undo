package ke.safeundo.app.nav

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import ke.safeundo.app.ui.SafeUndoViewModel
import ke.safeundo.app.ui.screens.*
import ke.safeundo.app.ui.theme.Su

@Composable
fun AppNav(vm: SafeUndoViewModel = viewModel()) {
    val nav = rememberNavController()
    val ui by vm.ui.collectAsStateWithLifecycle()

    Box(Modifier.fillMaxSize().background(Su.Bg)) {
        NavHost(nav, startDestination = "home") {
            composable("home") {
                HomeScreen(vm, onSend = { nav.navigate("send") }, onLipa = { nav.navigate("lipa") }, onSafeUndo = { nav.navigate("safeundo") })
            }
            composable("send") {
                PayScreen(vm, "Send Money", SEND_TABS, onBack = { nav.popBackStack() }, onContinue = { nav.navigate("confirm") })
            }
            composable("lipa") {
                PayScreen(vm, "Lipa na M-PESA", LIPA_TABS, onBack = { nav.popBackStack() }, onContinue = { nav.navigate("confirm") })
            }
            composable("confirm") {
                ConfirmScreen(vm, onBack = { nav.popBackStack() }, onDone = {
                    nav.navigate("success") { popUpTo("home") }
                })
            }
            composable("success") {
                SuccessScreen(
                    vm,
                    onClose = { nav.popBackStack("home", inclusive = false) },
                    onCase = { ref -> nav.navigate("case/$ref") { popUpTo("home") } },
                )
            }
            composable("safeundo") {
                SafeUndoScreen(vm, onBack = { nav.popBackStack() }, onCase = { ref -> nav.navigate("case/$ref") })
            }
            composable("case/{ref}", arguments = listOf(navArgument("ref") { type = NavType.StringType })) { entry ->
                CaseScreen(vm, entry.arguments?.getString("ref").orEmpty(), onBack = { nav.popBackStack() })
            }
        }

        ui.error?.let { msg ->
            Row(
                Modifier.align(Alignment.BottomCenter).navigationBarsPadding().padding(16.dp).fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp)).background(Su.Raised).padding(horizontal = 16.dp, vertical = 12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(msg, Modifier.weight(1f), color = Su.Text, fontSize = 14.sp)
                Text("Dismiss", color = Su.Green, fontWeight = FontWeight.SemiBold, modifier = Modifier.clickable { vm.clearError() }.padding(start = 12.dp))
            }
        }
    }
}
