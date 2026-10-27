package ke.safeundo.app.ui

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import ke.safeundo.app.data.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

data class UiState(
    val customers: List<Customer> = emptyList(),
    val customerId: String? = null,
    val profile: CustomerProfile? = null,
    val recentTx: List<TxSummary> = emptyList(),
    val cases: List<CaseListItem> = emptyList(),
    val activeCase: CaseDetail? = null,
    val error: String? = null,
)

/** What the user is about to pay. recipient is the normalised number / till / business number. */
data class Draft(
    val txType: String = "send_money",
    val recipient: String = "",
    val recipientName: String? = null,
    val amount: Double = 0.0,
    val accountRef: String = "",
)

/** One ViewModel for the whole simulated flow; all intelligence lives in the shared backend. */
class SafeUndoViewModel : ViewModel() {
    private val api = ApiClient.api

    private val _ui = MutableStateFlow(UiState())
    val ui: StateFlow<UiState> = _ui.asStateFlow()
    private val _draft = MutableStateFlow(Draft())
    val draft: StateFlow<Draft> = _draft.asStateFlow()
    private val _warning = MutableStateFlow<ScoreResult?>(null)
    val warning: StateFlow<ScoreResult?> = _warning.asStateFlow()
    private val _lastTx = MutableStateFlow<TxResult?>(null)
    val lastTx: StateFlow<TxResult?> = _lastTx.asStateFlow()
    private val _lookupName = MutableStateFlow<String?>(null)
    val lookupName: StateFlow<String?> = _lookupName.asStateFlow()
    private val _busy = MutableStateFlow(false)
    val busy: StateFlow<Boolean> = _busy.asStateFlow()

    init { start() }

    private fun run(block: suspend () -> Unit) = viewModelScope.launch {
        _busy.value = true
        try {
            block()
            _ui.update { it.copy(error = null) }
        } catch (e: CancellationException) {
            throw e
        } catch (e: Exception) {
            _ui.update { it.copy(error = e.friendly()) }
        } finally {
            _busy.value = false
        }
    }

    fun start() { run {
        val list = api.customers()
        val id = _ui.value.customerId ?: list.first().id
        _ui.update { it.copy(customers = list, customerId = id) }
        refresh(id)
    } }

    private suspend fun refresh(id: String) {
        val profile = api.profile(id)
        val tx = api.transactions(id, 6)
        val cases = api.cases(id)
        _ui.update { it.copy(profile = profile, recentTx = tx, cases = cases) }
    }

    fun reload() { _ui.value.customerId?.let { id -> run { refresh(id) } } }
    fun clearError() = _ui.update { it.copy(error = null) }

    fun selectCustomer(id: String) {
        _draft.value = Draft(); _warning.value = null; _lastTx.value = null; _lookupName.value = null
        run { _ui.update { it.copy(customerId = id, activeCase = null) }; refresh(id) }
    }

    fun lookupRecipient(txType: String, number: String) {
        val id = _ui.value.customerId ?: return
        viewModelScope.launch {
            _lookupName.value = try { api.lookup(id, txType, number).name } catch (e: Exception) { null }
        }
    }
    fun clearLookup() { _lookupName.value = null }

    /** Ask SafeUndo about the payment. Flagged -> warning sheet; otherwise continue straight on. */
    fun prepare(d: Draft, onProceed: () -> Unit) {
        val id = _ui.value.customerId ?: return
        _draft.value = d.copy(recipientName = _lookupName.value)
        run {
            val r = api.score(ScoreRequest(id, d.txType, d.recipient, d.amount))
            if (r.flagged) _warning.value = r else onProceed()
        }
    }
    fun dismissWarning() { _warning.value = null }

    fun send(onDone: () -> Unit) {
        val id = _ui.value.customerId ?: return
        val d = _draft.value
        run {
            _lastTx.value = api.createTx(TxRequest(id, d.txType, d.recipient, d.amount, d.recipientName))
            refresh(id)
            onDone()
        }
    }

    fun reportMistake(txId: String, reason: String, onOpened: (String) -> Unit) {
        val id = _ui.value.customerId ?: return
        run {
            val c = api.openCase(CaseRequest(id, txId, reason))
            _ui.update { it.copy(activeCase = c) }
            refresh(id)
            onOpened(c.ref)
        }
    }

    fun loadCase(ref: String) {
        _ui.update { s -> s.copy(activeCase = s.activeCase?.takeIf { it.ref == ref }) }
        run { _ui.update { it.copy(activeCase = api.caseDetail(ref)) } }
    }

    fun advance(ref: String) {
        val id = _ui.value.customerId ?: return
        run {
            val c = api.advance(ref, AdvanceRequest(4.0))
            _ui.update { it.copy(activeCase = c) }
            refresh(id)
        }
    }

    fun resetDemo() = run {
        api.reset()
        _ui.update { it.copy(activeCase = null) }
        _ui.value.customerId?.let { refresh(it) }
    }
}
