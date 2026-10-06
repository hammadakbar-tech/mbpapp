package com.merabrandpakistan.app.data

data class Hall(
    val id: String,
    val name: String,
    val description: String,
)

data class Exhibitor(
    val id: String, // also the exhibitor's login ID
    val name: String,
    val category: String,
    val tagline: String,
    val description: String,
    val hallId: String,
    val booth: String,
    val email: String,
    val phone: String,
)

data class Product(
    val id: String,
    val exhibitorId: String,
    val name: String,
    val description: String,
)

data class Visitor(
    val id: String,
    val name: String,
    val email: String,
    val company: String,
    val phone: String,
)

enum class MeetingStatus { PENDING, ACCEPTED, DECLINED }

data class MeetingRequest(
    val id: String,
    val visitorId: String,
    val visitorName: String,
    val visitorCompany: String,
    val exhibitorId: String,
    val slot: String,
    val message: String,
    val status: MeetingStatus,
    val createdAt: Long,
)

/** Who is signed in. Exhibitors are never created in the app; visitors register themselves. */
sealed interface Session {
    data object LoggedOut : Session
    data class ExhibitorSession(val exhibitorId: String) : Session
    data class VisitorSession(val visitorId: String) : Session
}
