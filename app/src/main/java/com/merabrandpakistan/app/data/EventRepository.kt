package com.merabrandpakistan.app.data

/**
 * Everything the app needs from a backend. [DemoRepository] implements it with sample data stored
 * on the device. To connect the real server, write another implementation that calls its API and
 * swap it in `EventViewModel`; no screen needs to change.
 */
interface EventRepository {
    suspend fun halls(): List<Hall>
    suspend fun exhibitors(): List<Exhibitor>
    suspend fun products(): List<Product>
    suspend fun meetingSlots(): List<String>

    suspend fun loginExhibitor(exhibitorId: String, pin: String): Result<Exhibitor>
    suspend fun registerVisitor(
        name: String,
        email: String,
        company: String,
        phone: String,
        password: String,
    ): Result<Visitor>
    suspend fun loginVisitor(email: String, password: String): Result<Visitor>
    suspend fun visitor(id: String): Visitor?

    suspend fun meetingsForExhibitor(exhibitorId: String): List<MeetingRequest>
    suspend fun meetingsForVisitor(visitorId: String): List<MeetingRequest>
    suspend fun requestMeeting(
        visitor: Visitor,
        exhibitorId: String,
        slot: String,
        message: String,
    ): Result<MeetingRequest>
    suspend fun respondToMeeting(meetingId: String, status: MeetingStatus): Result<Unit>

    fun savedSession(): Session
    fun saveSession(session: Session)
}
