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
    @SerialName("new_recipient") val newRecipient: Boolean = false,
    val message: String = "", val options: List<String> = emptyList(),
)

@Serializable data class ScoreResult(
    val flagged: Boolean,
    @SerialName("risk_score") val riskScore: Double,
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

object ApiClient {
    val api: SafeUndoApi by lazy {
        val http = OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS).readTimeout(20, TimeUnit.SECONDS).build()
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .client(http)
            .addConverterFactory(AppJson.asConverterFactory("application/json".toMediaType()))
            .build().create(SafeUndoApi::class.java)
    }
}

fun Throwable.friendly(): String = when (this) {
    is HttpException -> runCatching {
        Regex("\"detail\"\\s*:\\s*\"([^\"]+)\"").find(response()?.errorBody()?.string().orEmpty())?.groupValues?.get(1)
    }.getOrNull() ?: "Request failed (${code()})"
    is IOException -> "Can't reach the SafeUndo server. Check that the backend is running."
    else -> message ?: "Something went wrong"
}
