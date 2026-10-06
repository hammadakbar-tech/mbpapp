package com.merabrandpakistan.app.data

import android.content.Context
import android.util.Patterns
import org.json.JSONArray
import org.json.JSONObject
import java.security.MessageDigest
import java.util.UUID

/**
 * Demo backend: the catalogue comes from [DemoData]; visitor accounts, meeting requests and the
 * signed-in session are kept in SharedPreferences on this device only.
 */
class DemoRepository(context: Context) : EventRepository {

    private val prefs = context.getSharedPreferences("mbp_demo_store", Context.MODE_PRIVATE)

    private class StoredVisitor(val visitor: Visitor, val passwordHash: String)

    init {
        if (!prefs.getBoolean(KEY_SEEDED, false)) seedMeetings()
    }

    override suspend fun halls() = DemoData.halls
    override suspend fun exhibitors() = DemoData.exhibitors
    override suspend fun products() = DemoData.products
    override suspend fun meetingSlots() = DemoData.meetingSlots

    // ---- Authentication ----------------------------------------------------------------------

    override suspend fun loginExhibitor(exhibitorId: String, pin: String): Result<Exhibitor> {
        val id = exhibitorId.trim().uppercase()
        val exhibitor = DemoData.exhibitors.firstOrNull { it.id == id }
        return if (exhibitor != null && DemoData.exhibitorPins[id] == pin.trim()) {
            Result.success(exhibitor)
        } else {
            Result.failure(Exception("Invalid exhibitor ID or PIN"))
        }
    }

    override suspend fun registerVisitor(
        name: String,
        email: String,
        company: String,
        phone: String,
        password: String,
    ): Result<Visitor> {
        val cleanEmail = email.trim().lowercase()
        when {
            name.isBlank() -> return fail("Please enter your name")
            !Patterns.EMAIL_ADDRESS.matcher(cleanEmail).matches() -> return fail("Please enter a valid email")
            password.length < 6 -> return fail("Password must be at least 6 characters")
        }
        val all = loadVisitors()
        if (all.any { it.visitor.email == cleanEmail }) return fail("An account with this email already exists")

        val visitor = Visitor(UUID.randomUUID().toString(), name.trim(), cleanEmail, company.trim(), phone.trim())
        saveVisitors(all + StoredVisitor(visitor, hash(cleanEmail, password)))
        return Result.success(visitor)
    }

    override suspend fun loginVisitor(email: String, password: String): Result<Visitor> {
        val cleanEmail = email.trim().lowercase()
        val match = loadVisitors().firstOrNull {
            it.visitor.email == cleanEmail && it.passwordHash == hash(cleanEmail, password)
        }
        return if (match != null) Result.success(match.visitor) else fail("Incorrect email or password")
    }

    override suspend fun visitor(id: String): Visitor? =
        loadVisitors().firstOrNull { it.visitor.id == id }?.visitor

    // ---- Meetings ----------------------------------------------------------------------------

    override suspend fun meetingsForExhibitor(exhibitorId: String) =
        loadMeetings().filter { it.exhibitorId == exhibitorId }.sortedByDescending { it.createdAt }

    override suspend fun meetingsForVisitor(visitorId: String) =
        loadMeetings().filter { it.visitorId == visitorId }.sortedByDescending { it.createdAt }

    override suspend fun requestMeeting(
        visitor: Visitor,
        exhibitorId: String,
        slot: String,
        message: String,
    ): Result<MeetingRequest> {
        val all = loadMeetings()
        val duplicate = all.any {
            it.visitorId == visitor.id && it.exhibitorId == exhibitorId &&
                it.slot == slot && it.status != MeetingStatus.DECLINED
        }
        if (duplicate) return fail("You already requested this time slot")

        val request = MeetingRequest(
            id = UUID.randomUUID().toString(),
            visitorId = visitor.id,
            visitorName = visitor.name,
            visitorCompany = visitor.company,
            exhibitorId = exhibitorId,
            slot = slot,
            message = message,
            status = MeetingStatus.PENDING,
            createdAt = System.currentTimeMillis(),
        )
        saveMeetings(all + request)
        return Result.success(request)
    }

    override suspend fun respondToMeeting(meetingId: String, status: MeetingStatus): Result<Unit> {
        val all = loadMeetings()
        if (all.none { it.id == meetingId }) return fail("Request not found")
        saveMeetings(all.map { if (it.id == meetingId) it.copy(status = status) else it })
        return Result.success(Unit)
    }

    // ---- Session -----------------------------------------------------------------------------

    override fun savedSession(): Session = when (prefs.getString(KEY_SESSION_ROLE, null)) {
        "exhibitor" -> Session.ExhibitorSession(prefs.getString(KEY_SESSION_ID, "").orEmpty())
        "visitor" -> Session.VisitorSession(prefs.getString(KEY_SESSION_ID, "").orEmpty())
        else -> Session.LoggedOut
    }

    override fun saveSession(session: Session) {
        val (role, id) = when (session) {
            Session.LoggedOut -> null to null
            is Session.ExhibitorSession -> "exhibitor" to session.exhibitorId
            is Session.VisitorSession -> "visitor" to session.visitorId
        }
        prefs.edit().putString(KEY_SESSION_ROLE, role).putString(KEY_SESSION_ID, id).apply()
    }

    // ---- Storage helpers ---------------------------------------------------------------------

    private fun <T> fail(message: String): Result<T> = Result.failure(Exception(message))

    private fun hash(email: String, password: String): String =
        MessageDigest.getInstance("SHA-256")
            .digest("$email:$password".toByteArray())
            .joinToString("") { "%02x".format(it) }

    private fun loadVisitors(): List<StoredVisitor> {
        val array = JSONArray(prefs.getString(KEY_VISITORS, "[]"))
        return (0 until array.length()).map { i ->
            val o = array.getJSONObject(i)
            StoredVisitor(
                Visitor(o.getString("id"), o.getString("name"), o.getString("email"), o.getString("company"), o.getString("phone")),
                o.getString("hash"),
            )
        }
    }

    private fun saveVisitors(list: List<StoredVisitor>) {
        val array = JSONArray()
        list.forEach {
            array.put(
                JSONObject()
                    .put("id", it.visitor.id)
                    .put("name", it.visitor.name)
                    .put("email", it.visitor.email)
                    .put("company", it.visitor.company)
                    .put("phone", it.visitor.phone)
                    .put("hash", it.passwordHash),
            )
        }
        prefs.edit().putString(KEY_VISITORS, array.toString()).apply()
    }

    private fun loadMeetings(): List<MeetingRequest> {
        val array = JSONArray(prefs.getString(KEY_MEETINGS, "[]"))
        return (0 until array.length()).map { i ->
            val o = array.getJSONObject(i)
            MeetingRequest(
                id = o.getString("id"),
                visitorId = o.getString("visitorId"),
                visitorName = o.getString("visitorName"),
                visitorCompany = o.getString("visitorCompany"),
                exhibitorId = o.getString("exhibitorId"),
                slot = o.getString("slot"),
                message = o.getString("message"),
                status = MeetingStatus.valueOf(o.getString("status")),
                createdAt = o.getLong("createdAt"),
            )
        }
    }

    private fun saveMeetings(list: List<MeetingRequest>) {
        val array = JSONArray()
        list.forEach {
            array.put(
                JSONObject()
                    .put("id", it.id)
                    .put("visitorId", it.visitorId)
                    .put("visitorName", it.visitorName)
                    .put("visitorCompany", it.visitorCompany)
                    .put("exhibitorId", it.exhibitorId)
                    .put("slot", it.slot)
                    .put("message", it.message)
                    .put("status", it.status.name)
                    .put("createdAt", it.createdAt),
            )
        }
        prefs.edit().putString(KEY_MEETINGS, array.toString()).apply()
    }

    /** A few sample requests so the exhibitor dashboard isn't empty on first login. */
    private fun seedMeetings() {
        val now = System.currentTimeMillis()
        fun sample(n: Int, name: String, company: String, exhibitor: String, slot: Int, msg: String, status: MeetingStatus) =
            MeetingRequest("seed-$n", "seed-visitor-$n", name, company, exhibitor, DemoData.meetingSlots[slot], msg, status, now - n * 3_600_000L)

        saveMeetings(
            listOf(
                sample(1, "Ayesha Khan", "Noor Retail", "EXH001", 0, "Interested in cotton poplin for our summer range.", MeetingStatus.PENDING),
                sample(2, "Bilal Ahmed", "Gulf Trading LLC", "EXH001", 3, "Would like to discuss export pricing.", MeetingStatus.PENDING),
                sample(3, "Sara Malik", "Fabric House UK", "EXH001", 1, "Following up on our email.", MeetingStatus.ACCEPTED),
                sample(4, "Usman Tariq", "Metro Mart", "EXH002", 2, "Looking for private-label denim.", MeetingStatus.PENDING),
            ),
        )
        prefs.edit().putBoolean(KEY_SEEDED, true).apply()
    }

    private companion object {
        const val KEY_SEEDED = "seeded"
        const val KEY_VISITORS = "visitors"
        const val KEY_MEETINGS = "meetings"
        const val KEY_SESSION_ROLE = "session_role"
        const val KEY_SESSION_ID = "session_id"
    }
}
