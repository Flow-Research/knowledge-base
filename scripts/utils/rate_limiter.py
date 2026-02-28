"""Rate limiting utilities for API calls."""

import time
from collections import deque
from datetime import datetime, timedelta


class RateLimiter:
    """Token bucket rate limiter for API calls."""

    def __init__(self, requests_per_minute: int = 50, tokens_per_minute: int = 150000):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
            tokens_per_minute: Maximum tokens per minute
        """
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute

        # Track request timestamps
        self.request_times = deque()

        # Track token usage
        self.token_usage = deque()

    def wait_if_needed(self, estimated_tokens: int = 0) -> None:
        """Wait if rate limit would be exceeded.

        Args:
            estimated_tokens: Estimated tokens for this request
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Remove old request times
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()

        # Remove old token usage
        while self.token_usage and self.token_usage[0][0] < one_minute_ago:
            self.token_usage.popleft()

        # Check request rate limit
        if len(self.request_times) >= self.requests_per_minute:
            wait_time = (
                self.request_times[0] + timedelta(minutes=1) - now
            ).total_seconds()
            if wait_time > 0:
                print(f"Rate limit: waiting {wait_time:.1f}s for request quota")
                time.sleep(wait_time)

        # Check token rate limit
        current_tokens = sum(usage[1] for usage in self.token_usage)
        if current_tokens + estimated_tokens > self.tokens_per_minute:
            # Wait for oldest tokens to expire
            if self.token_usage:
                wait_time = (
                    self.token_usage[0][0] + timedelta(minutes=1) - now
                ).total_seconds()
                if wait_time > 0:
                    print(f"Rate limit: waiting {wait_time:.1f}s for token quota")
                    time.sleep(wait_time)

        # Record this request
        self.request_times.append(datetime.now())
        if estimated_tokens > 0:
            self.token_usage.append((datetime.now(), estimated_tokens))

    def record_usage(self, actual_tokens: int) -> None:
        """Record actual token usage after request.

        Args:
            actual_tokens: Actual tokens used
        """
        # Update the most recent token usage with actual value
        if self.token_usage:
            last_time = self.token_usage[-1][0]
            self.token_usage[-1] = (last_time, actual_tokens)

    def get_stats(self) -> dict:
        """Get rate limiter statistics.

        Returns:
            Dict with current usage stats
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        # Count recent requests
        recent_requests = sum(
            1 for req_time in self.request_times if req_time >= one_minute_ago
        )

        # Count recent tokens
        recent_tokens = sum(
            usage[1] for usage in self.token_usage if usage[0] >= one_minute_ago
        )

        return {
            "requests_last_minute": recent_requests,
            "requests_limit": self.requests_per_minute,
            "tokens_last_minute": recent_tokens,
            "tokens_limit": self.tokens_per_minute,
            "request_quota_remaining": max(
                0, self.requests_per_minute - recent_requests
            ),
            "token_quota_remaining": max(0, self.tokens_per_minute - recent_tokens),
        }
