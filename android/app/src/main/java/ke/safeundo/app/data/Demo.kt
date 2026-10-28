package ke.safeundo.app.data

data class PaybillOption(val name: String, val businessNumber: String, val sampleAccount: String)

/**
 * Stand-in for the phone's contact book and merchant directory (a real app would read device contacts).
 * Numbers match the synthetic seed data on the backend. Till numbers, PayBill business numbers,
 * and PayBill account numbers are all distinct.
 */
object DemoContacts {
    private val byCustomer = mapOf(
        "cust_amina" to listOf("Mama Wanjiru" to "0700123401", "Kevin Otieno" to "0700123402", "Faith Njeri" to "0700123403"),
        "cust_brian" to listOf("Stockist Hassan" to "0700223401", "Njoroge Supplies" to "0700223402", "Mercy Wambui" to "0700223403"),
        "cust_grace" to listOf("Mum" to "0700323401", "Tabitha Roommate" to "0700323402", "Campus Cafe" to "0700323403"),
    )
    val buyGoodsTills = listOf(
        "Njoroge Hardware" to "523417",
        "Naivas Supermarket" to "841209",
        "Java House" to "619304",
        "Quickmart" to "738291",
    )
    val paybills = listOf(
        PaybillOption("Equity Paybill", "247247", "ACC001"),
        PaybillOption("KPLC Prepaid", "888880", "MTR-77412"),
        PaybillOption("Co-op Bank", "400200", "14289901"),
        PaybillOption("KCB Paybill", "522522", "INV-2049"),
    )
    val paybillAccounts = listOf("ACC001", "MTR-77412", "14289901", "INV-2049")
    val demoPhoneChips = listOf(
        "0700123401" to "Usual contact",
        "0799999999" to "New number",
        "0712345678" to "New number",
    )
    val pochiChips = listOf(
        "0700123401" to "Mama Wanjiru",
        "0700223401" to "Stockist Hassan",
        "0799999999" to "New Pochi",
        "0745112233" to "New Pochi",
    )

    fun forCustomer(id: String?): List<Pair<String, String>> = byCustomer[id].orEmpty()
}
