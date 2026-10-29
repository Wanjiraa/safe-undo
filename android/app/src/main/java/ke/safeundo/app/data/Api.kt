package ke.safeundo.app.data

import ke.safeundo.app.BuildConfig
import kotlinx.serialization.ExperimentalSerializationApi
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import retrofit2.HttpException
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import retrofit2.http.Query
import java.io.IOException
import java.util.concurrent.TimeUnit

// ---------- models (field names mirror the FastAPI backend) ----------

@Serializable data class Customer(
    val id: String, val name: String,
    @SerialName("msisdn_masked") val msisdnMasked: String, val balance: Double,
)

@Serializable data class TypicalAmount(val median: Int, val p25: Int, val p75: Int)
@Serializable data class Contact(val name: String? = null, val masked: String? = null)

@Serializable data class CustomerProfile(
    val id: String, val name: String,
    @SerialName("msisdn_masked") val msisdnMasked: String, val balance: Double,
    @SerialName("history_size") val historySize: Int = 0,
    @SerialName("typical_amount") val typicalAmount: TypicalAmount,
    @SerialName("frequent_contacts") val frequentContacts: List<Contact> = emptyList(),
)

@Serializable data class Lookup(val name: String, val known: Boolean = false)

@Serializable data class ScoreRequest(
    @SerialName("customer_id") val customerId: String,
    @SerialName("tx_type") val txType: String,
    val recipient: String, val amount: Double,
)

@Serializable data class Warning(
    val title: String, val amount: Double, val recipient: String,
    @SerialName("recipient_masked") val recipientMasked: String? = null,
    @SerialName("recipient_name") val recipientName: String? = null,
    @SerialName("new_recipient") val newRecipient: Boolean = false,
    val message: String = "", val options: List<String> = emptyList(),
)

@Serializable data class ScoreResult(
    val flagged: Boolean,
    @SerialName("risk_score") val riskScore: Double,
    @SerialName("recipient_name") val recipientName: String? = null,
    val reasons: List<String> = emptyList(),
    val warning: Warning? = null,
    @SerialName("low_confidence") val lowConfidence: Boolean = false,
)

@Serializable data class TxRequest(
    @SerialName("customer_id") val customerId: String,
    @SerialName("tx_type") val txType: String,
    val recipient: String, val amount: Double,
    @SerialName("recipient_name") val recipientName: String? = null,
)

@Serializable data class TxResult(
    val id: String,
    @SerialName("mpesa_ref") val mpesaRef: String,
    @SerialName("tx_type") val txType: String,
    @SerialName("tx_type_label") val txTypeLabel: String,
    val amount: Double,
    @SerialName("transaction_cost") val transactionCost: Double = 0.0,
    val ts: String, val recipient: String,
    @SerialName("recipient_name") val recipientName: String? = null,
    val balance: Double,
)

@Serializable data class TxSummary(
    val id: String,
    @SerialName("mpesa_ref") val mpesaRef: String,
    @SerialName("tx_type") val txType: String,
    @SerialName("tx_type_label") val txTypeLabel: String,
    val amount: Double, val ts: String, val recipient: String,
    @SerialName("recipient_name") val recipientName: String? = null,
    @SerialName("has_open_case") val hasOpenCase: Boolean = false,
)

@Serializable data class CaseRequest(
    @SerialName("customer_id") val customerId: String,
    @SerialName("transaction_id") val transactionId: String,
    val reason: String,
)

@Serializable data class AdvanceRequest(val hours: Double = 4.0)

@Serializable data class Prediction(
    @SerialName("remaining_hours") val remainingHours: Double,
    val label: String,
    @SerialName("delay_risk") val delayRisk: Double,
    @SerialName("risk_level") val riskLevel: String,
    @SerialName("elapsed_hours") val elapsedHours: Double = 0.0,
    val overdue: Boolean = false,
    val why: List<String> = emptyList(),
    val action: String = "",
)

@Serializable data class TimelineStep(val status: String, val label: String, val reached: Boolean)
@Serializable data class HistoryEntry(val status: String, val label: String, val ts: String, val note: String? = null)

@Serializable data class Guidance(
    val title: String, val steps: List<String>,
    @SerialName("verified_procedure") val verifiedProcedure: Boolean = false,
    val note: String = "", val disclaimer: String = "",
)

@Serializable data class CaseDetail(
    val ref: String,
    @SerialName("reason_label") val reasonLabel: String,
    val status: String,
    @SerialName("status_label") val statusLabel: String,
    @SerialName("submitted_at") val submittedAt: String,
    @SerialName("rejection_reason") val rejectionReason: String? = null,
    val simulated: Boolean = true,
    val transaction: TxSummary,
    val history: List<HistoryEntry> = emptyList(),
    val timeline: List<TimelineStep> = emptyList(),
    val prediction: Prediction? = null,
    val guidance: Guidance,
    val disclaimer: String = "",
    val duplicate: Boolean = false,
)

@Serializable data class CaseListItem(
    val ref: String, val status: String,
    @SerialName("status_label") val statusLabel: String,
    @SerialName("reason_label") val reasonLabel: String,
    val transaction: TxSummary, val prediction: Prediction? = null,
)

// ---------- API ----------

interface SafeUndoApi {
    @GET("api/customers") suspend fun customers(): List<Customer>
    @GET("api/customers/{id}") suspend fun profile(@Path("id") id: String): CustomerProfile
    @GET("api/customers/{id}/transactions")
    suspend fun transactions(@Path("id") id: String, @Query("limit") limit: Int = 6): List<TxSummary>
    @GET("api/customers/{id}/cases") suspend fun cases(@Path("id") id: String): List<CaseListItem>
    @GET("api/recipients/lookup")
    suspend fun lookup(@Query("customer_id") customerId: String, @Query("tx_type") txType: String, @Query("number") number: String): Lookup
    @POST("api/protect/score") suspend fun score(@Body body: ScoreRequest): ScoreResult
    @POST("api/transactions") suspend fun createTx(@Body body: TxRequest): TxResult
    @POST("api/cases") suspend fun openCase(@Body body: CaseRequest): CaseDetail
    @GET("api/cases/{ref}") suspend fun caseDetail(@Path("ref") ref: String): CaseDetail
    @POST("api/cases/{ref}/simulate-advance") suspend fun advance(@Path("ref") ref: String, @Body body: AdvanceRequest): CaseDetail
    @POST("api/demo/reset") suspend fun reset(): Map<String, String>
}

@OptIn(ExperimentalSerializationApi::class)
val AppJson = Json { ignoreUnknownKeys = true; coerceInputValues = true; encodeDefaults = true; explicitNulls = false }

object LocalFallbackEngine {
    private val balances = mutableMapOf(
        "cust_amina" to 24310.50,
        "cust_brian" to 8420.00,
        "cust_grace" to 62900.00,
    )
    private val medians = mapOf("cust_amina" to 800, "cust_brian" to 450, "cust_grace" to 2500)
    private val directory = mapOf(
        "0700123401" to "MAMA WANJIRU",
        "0700123402" to "PETER KAMAU",
        "0700123403" to "JOHN OTIENO",
        "0700223401" to "MARY NJERI",
        "0700323401" to "DAVID KIPROP",
        "0799999999" to "NANCY KAMAU",
        "0712345678" to "JAMES MWANGI",
        "0722000111" to "WANJIKU GROCERS",
        "0711222333" to "MAMA MBOGA",
        "0798765432" to "BENSON KARIUKI",
        "523417" to "JAVA HOUSE KIMATHI",
        "841209" to "NAIVAS SUPERMARKET",
        "619304" to "QUICKMART KILIMANI",
        "738291" to "GOODLIFE PHARMACY",
        "904512" to "TOTALENERGIES HURLINGHAM",
        "247247" to "EQUITY PAYBILL",
        "888880" to "KPLC PREPAID",
        "400200" to "CO-OP BANK PAYBILL",
        "522522" to "KCB PAYBILL",
        "303030" to "ABSA BANK PAYBILL",
    )

    private val txStore = mutableMapOf(
        "cust_amina" to mutableListOf(
            TxSummary("tx_1001", "SJK49L2M1P", "send_money", "Send Money", 2500.0, "2026-10-28 14:12", "0799***999", "NANCY KAMAU", true),
            TxSummary("tx_1002", "SJK31A8Q9R", "send_money", "Send Money", 800.0, "2026-10-28 09:40", "0700***401", "MAMA WANJIRU", false),
            TxSummary("tx_1003", "SJK18P4T2W", "buy_goods", "Buy Goods (Till)", 1450.0, "2026-10-27 19:15", "841***209", "NAIVAS SUPERMARKET", false),
        ),
        "cust_brian" to mutableListOf(
            TxSummary("tx_2001", "SJK72M9K4L", "send_money", "Send Money", 450.0, "2026-10-28 11:20", "0700***401", "MARY NJERI", false),
        ),
        "cust_grace" to mutableListOf(
            TxSummary("tx_3001", "SJK90R3V7N", "paybill", "PayBill", 3200.0, "2026-10-28 10:05", "888***880", "KPLC PREPAID", false),
        ),
    )

    private val caseStore = mutableMapOf(
        "SU-1042" to CaseDetail(
            ref = "SU-1042",
            reasonLabel = "Wrong recipient number",
            status = "under_review",
            statusLabel = "Under review",
            submittedAt = "2026-10-28 14:18",
            rejectionReason = null,
            simulated = true,
            transaction = TxSummary("tx_1001", "SJK49L2M1P", "send_money", "Send Money", 2500.0, "2026-10-28 14:12", "0799***999", "NANCY KAMAU", true),
            history = listOf(
                HistoryEntry("submitted", "Submitted", "2026-10-28 14:18", "Reversal request logged in SafeUndo"),
                HistoryEntry("under_review", "Under review", "2026-10-28 14:45", "Recipient consent & account balance check in progress (Simulated)"),
            ),
            timeline = listOf(
                TimelineStep("submitted", "Submitted", true),
                TimelineStep("under_review", "Under review", true),
                TimelineStep("completed", "Completed", false),
            ),
            prediction = Prediction(
                remainingHours = 7.5,
                label = "Est. 5–9 hours (~7.5h remaining)",
                delayRisk = 0.08,
                riskLevel = "Low",
                elapsedHours = 2.0,
                overdue = false,
                why = listOf("Reported within 10 minutes of transfer", "Send Money reversal path has highest completion rate"),
                action = "Forward the original M-PESA confirmation SMS to 456 if you haven't already, and keep your line active.",
            ),
            guidance = Guidance(
                title = "Send Money reversal steps",
                steps = listOf(
                    "Forward the original M-PESA confirmation SMS to 456 immediately.",
                    "Wait for the official M-PESA acknowledgement SMS.",
                    "Do not call or send extra money to the recipient directly.",
                ),
                verifiedProcedure = true,
                note = "Standard M-PESA Send Money reversal procedure via 456.",
                disclaimer = "Simulated status for hackathon demo — SafeUndo guides and tracks but does not reverse funds itself.",
            ),
            disclaimer = "Simulated status for hackathon demo.",
        )
    )

    fun customers(): List<Customer> = listOf(
        Customer("cust_amina", "Amina Wanjiru", "0712***890", balances["cust_amina"] ?: 24310.50),
        Customer("cust_brian", "Brian Otieno", "0723***451", balances["cust_brian"] ?: 8420.00),
        Customer("cust_grace", "Grace Muthoni", "0734***112", balances["cust_grace"] ?: 62900.00),
    )

    fun profile(id: String): CustomerProfile {
        val c = customers().find { it.id == id } ?: customers().first()
        val med = medians[c.id] ?: 800
        return CustomerProfile(
            id = c.id, name = c.name, msisdnMasked = c.msisdnMasked, balance = c.balance,
            historySize = 60, typicalAmount = TypicalAmount(med, med / 2, med * 2),
            frequentContacts = listOf(Contact("MAMA WANJIRU", "0700***401"), Contact("PETER KAMAU", "0700***402")),
        )
    }

    fun lookup(txType: String, number: String): Lookup {
        val clean = number.trim().replace(" ", "")
        val base = clean.split("#").firstOrNull().orEmpty()
        val name = directory[base] ?: when (txType) {
            "buy_goods" -> "VERIFIED TILL $base"
            "paybill" -> "VERIFIED PAYBILL $base"
            "pochi" -> "BIASHARA ACCOUNT ${base.takeLast(4)}"
            else -> "REGISTERED USER ${base.takeLast(4)}"
        }
        return Lookup(name = name, known = directory.containsKey(base))
    }

    fun score(body: ScoreRequest): ScoreResult {
        val lk = lookup(body.txType, body.recipient)
        val med = (medians[body.customerId] ?: 800).toDouble()
        val bal = balances[body.customerId] ?: 24310.50
        val reasons = mutableListOf<String>()
        if (body.amount >= med * 3.0 && body.amount >= 2500.0) {
            reasons.add("This amount is higher than what you usually transact. Please confirm the recipient name and amount.")
        }
        if (body.amount >= bal * 0.65) {
            reasons.add("This payment is a large portion (${((body.amount / bal) * 100).toInt()}%) of your current balance.")
        }
        val flagged = reasons.isNotEmpty()
        val risk = if (flagged) 0.92 else 0.12
        return ScoreResult(
            flagged = flagged,
            riskScore = risk,
            recipientName = lk.name,
            reasons = reasons,
            warning = if (flagged) Warning(
                title = "Unusual transaction detected",
                amount = body.amount,
                recipient = lk.name,
                recipientMasked = lk.name,
                recipientName = lk.name,
                newRecipient = !lk.known,
                message = reasons.joinToString(" "),
                options = listOf("Yes, continue", "Cancel"),
            ) else null,
        )
    }

    fun createTx(body: TxRequest): TxResult {
        val lk = lookup(body.txType, body.recipient)
        val rName = body.recipientName ?: lk.name
        val bal = (balances[body.customerId] ?: 24310.50) - body.amount
        balances[body.customerId] = bal
        val ref = "SJK" + (100000..999999).random().toString()
        val id = "tx_" + System.currentTimeMillis()
        val label = when (body.txType) {
            "pochi" -> "Pochi la Biashara"
            "buy_goods" -> "Buy Goods (Till)"
            "paybill" -> "PayBill"
            else -> "Send Money"
        }
        val summary = TxSummary(id, ref, body.txType, label, body.amount, "Just now", body.recipient, rName, false)
        txStore.getOrPut(body.customerId) { mutableListOf() }.add(0, summary)
        return TxResult(id, ref, body.txType, label, body.amount, 0.0, "Just now", body.recipient, rName, bal)
    }

    fun transactions(id: String, limit: Int): List<TxSummary> =
        txStore[id]?.take(limit) ?: txStore["cust_amina"]!!.take(limit)

    fun cases(id: String): List<CaseListItem> = caseStore.values.map {
        CaseListItem(it.ref, it.status, it.statusLabel, it.reasonLabel, it.transaction, it.prediction)
    }

    fun openCase(body: CaseRequest): CaseDetail {
        val tx = txStore.values.flatten().find { it.id == body.transactionId }
            ?: TxSummary(body.transactionId, "SJK88N2P1Q", "send_money", "Send Money", 2000.0, "Just now", "0799***999", "NANCY KAMAU", true)
        val ref = "SU-" + (1050..1099).random()
        val detail = caseStore["SU-1042"]!!.copy(
            ref = ref,
            status = "submitted",
            statusLabel = "Submitted",
            submittedAt = "Just now",
            transaction = tx.copy(hasOpenCase = true),
        )
        caseStore[ref] = detail
        return detail
    }

    fun caseDetail(ref: String): CaseDetail = caseStore[ref] ?: caseStore["SU-1042"]!!

    fun advance(ref: String, hours: Double): CaseDetail {
        val cur = caseDetail(ref)
        val next = when (cur.status) {
            "submitted" -> cur.copy(
                status = "under_review",
                statusLabel = "Under review",
                timeline = listOf(
                    TimelineStep("submitted", "Submitted", true),
                    TimelineStep("under_review", "Under review", true),
                    TimelineStep("completed", "Completed", false),
                )
            )
            else -> cur.copy(
                status = "completed",
                statusLabel = "Completed (Simulated)",
                prediction = null,
                timeline = listOf(
                    TimelineStep("submitted", "Submitted", true),
                    TimelineStep("under_review", "Under review", true),
                    TimelineStep("completed", "Completed", true),
                ),
                history = cur.history + HistoryEntry("completed", "Completed (Simulated)", "Simulated +${hours.toInt()}h", "Simulated reversal completed and credited back.")
            )
        }
        caseStore[ref] = next
        return next
    }
}

object ApiClient {
    private val fallbackHosts = listOf("127.0.0.1", "10.12.134.121", "10.73.254.121", "10.0.2.2", "10.76.110.121")
    @Volatile private var preferredHost: String = "127.0.0.1"

    private val remoteApi: SafeUndoApi by lazy {
        val http = OkHttpClient.Builder()
            .connectTimeout(900, TimeUnit.MILLISECONDS)
            .readTimeout(8, TimeUnit.SECONDS)
            .addInterceptor { chain ->
                val req = chain.request()
                val orderedHosts = listOf(preferredHost) + fallbackHosts.filter { it != preferredHost }
                var lastErr: IOException? = null
                for (host in orderedHosts) {
                    val url = req.url.newBuilder().scheme("http").host(host).port(8000).build()
                    try {
                        val resp = chain.proceed(req.newBuilder().url(url).build())
                        preferredHost = host
                        return@addInterceptor resp
                    } catch (e: IOException) {
                        lastErr = e
                    }
                }
                throw lastErr ?: IOException("Backend unreachable")
            }
            .build()
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(http)
            .addConverterFactory(AppJson.asConverterFactory("application/json".toMediaType()))
            .build().create(SafeUndoApi::class.java)
    }

    val api: SafeUndoApi = object : SafeUndoApi {
        override suspend fun customers(): List<Customer> =
            try { remoteApi.customers() } catch (_: Exception) { LocalFallbackEngine.customers() }
        override suspend fun profile(id: String): CustomerProfile =
            try { remoteApi.profile(id) } catch (_: Exception) { LocalFallbackEngine.profile(id) }
        override suspend fun transactions(id: String, limit: Int): List<TxSummary> =
            try { remoteApi.transactions(id, limit) } catch (_: Exception) { LocalFallbackEngine.transactions(id, limit) }
        override suspend fun cases(id: String): List<CaseListItem> =
            try { remoteApi.cases(id) } catch (_: Exception) { LocalFallbackEngine.cases(id) }
        override suspend fun lookup(customerId: String, txType: String, number: String): Lookup =
            try { remoteApi.lookup(customerId, txType, number) } catch (_: Exception) { LocalFallbackEngine.lookup(txType, number) }
        override suspend fun score(body: ScoreRequest): ScoreResult =
            try { remoteApi.score(body) } catch (_: Exception) { LocalFallbackEngine.score(body) }
        override suspend fun createTx(body: TxRequest): TxResult =
            try { remoteApi.createTx(body) } catch (_: Exception) { LocalFallbackEngine.createTx(body) }
        override suspend fun openCase(body: CaseRequest): CaseDetail =
            try { remoteApi.openCase(body) } catch (_: Exception) { LocalFallbackEngine.openCase(body) }
        override suspend fun caseDetail(ref: String): CaseDetail =
            try { remoteApi.caseDetail(ref) } catch (_: Exception) { LocalFallbackEngine.caseDetail(ref) }
        override suspend fun advance(ref: String, body: AdvanceRequest): CaseDetail =
            try { remoteApi.advance(ref, body) } catch (_: Exception) { LocalFallbackEngine.advance(ref, body.hours) }
        override suspend fun reset(): Map<String, String> =
            try { remoteApi.reset() } catch (_: Exception) { mapOf("status" to "ok") }
    }
}

fun Throwable.friendly(): String = when (this) {
    is HttpException -> runCatching {
        Regex("\"detail\"\\s*:\\s*\"([^\"]+)\"").find(response()?.errorBody()?.string().orEmpty())?.groupValues?.get(1)
    }.getOrNull() ?: "Request failed (${code()})"
    is IOException -> "Can't reach the SafeUndo server. Check that the backend is running."
    else -> message ?: "Something went wrong"
}
