"""Bounded single-process admission. Trusted edge limits still required for launch."""
from collections import deque
from threading import Lock, BoundedSemaphore
from time import monotonic
from fastapi import HTTPException

slots=BoundedSemaphore(4)


class RateLimiter:
    def __init__(self):self.lock=Lock();self.clients={};self.global_requests=deque()

    def check(self,host):
        now=monotonic()
        with self.lock:
            self.clients={k:v for k,v in self.clients.items() if v and v[-1]>now-60}
            while self.global_requests and self.global_requests[0]<=now-60:self.global_requests.popleft()
            requests=self.clients.get(host,deque())
            while requests and requests[0]<=now-60:requests.popleft()
            if len(requests)>=20 or len(self.global_requests)>=120 or (host not in self.clients and len(self.clients)>=2048):
                raise HTTPException(429,'Evidence query limit exceeded',headers={'Retry-After':'60'})
            requests.append(now);self.clients[host]=requests;self.global_requests.append(now)


limiter=RateLimiter()
