package ke.safeundo.app.data

/**
 * Stand-in for the phone's contact book (a real app would read device contacts).
 * Numbers match the synthetic seed data on the backend. They are fictional.
 */
object DemoContacts {
    private val byCustomer = mapOf(
        "cust_amina" to listOf("Mama Wanjiru" to "0700123401", "Kevin Otieno" to "0700123402", "Faith Njeri" to "0700123403"),
        "cust_brian" to listOf("Stockist Hassan" to "0700223401", "Njoroge Supplies" to "0700223402", "Mercy Wambui" to "0700223403"),
        "cust_grace" to listOf("Mum" to "0700323401", "Tabitha Roommate" to "0700323402", "Campus Cafe" to "0700323403"),
    )
    fun forCustomer(id: String?): List<Pair<String, String>> = byCustomer[id].orEmpty()
}
