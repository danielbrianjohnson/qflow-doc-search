from rest_framework.throttling import AnonRateThrottle


class UploadRateThrottle(AnonRateThrottle):
    scope = "upload"


class SearchRateThrottle(AnonRateThrottle):
    scope = "search"
