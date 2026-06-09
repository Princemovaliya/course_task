from rest_framework.throttling import UserRateThrottle


class EnrollmentUserRateThrottle(UserRateThrottle):
    """Rate limit enrollment create/cancel to reduce abuse and race-condition pressure."""

    scope = "enrollment"
