import os
import random
import string
import gevent
from locust import HttpUser, task, between, events

WARMUP_SECONDS = int(os.environ.get("WARMUP_SECONDS", "60"))

def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters, k=length))

def random_phone():
    return ''.join(random.choices(string.digits, k=10))

class PetClinicBaseUser(HttpUser):
    # Wait time between tasks: 100ms to 300ms simulating active realistic client interaction
    wait_time = between(0.1, 0.3)
    
    def get_owners(self):
        """GET /owners -> 45% (Perfil 1) / 20% (Perfil 2)"""
        with self.client.get(
            "/api/customer/owners",
            name="GET /owners",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    def get_owner_by_id(self):
        """GET /owners/{id} -> 35% (Perfil 1) / 20% (Perfil 2)"""
        owner_id = random.randint(1, 10)
        with self.client.get(
            f"/api/customer/owners/{owner_id}",
            name="GET /owners/{id}",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    def get_vets(self):
        """GET /vets -> 15% (Perfil 1) / 20% (Perfil 2)"""
        with self.client.get(
            "/api/vet/vets",
            name="GET /vets",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status {response.status_code}")

    def post_owner(self):
        """POST /owners -> 5% (Perfil 1) / 40% (Perfil 2)"""
        payload = {
            "firstName": f"User_{random_string(6)}",
            "lastName": f"Test_{random_string(6)}",
            "address": f"{random.randint(10, 999)} Main Street",
            "city": "Springfield",
            "telephone": random_phone()
        }
        with self.client.post(
            "/api/customer/owners",
            json=payload,
            name="POST /owners",
            catch_response=True
        ) as response:
            if response.status_code in (200, 201):
                response.success()
            else:
                response.failure(f"Status {response.status_code}")


class PerfilLeituraUser(PetClinicBaseUser):
    """
    Perfil 1 — Leitura:
    GET /owners:       45%
    GET /owners/{id}:  35%
    GET /vets:         15%
    POST /owners:       5%
    """
    weight = 1

    @task(45)
    def task_get_owners(self):
        self.get_owners()

    @task(35)
    def task_get_owner_by_id(self):
        self.get_owner_by_id()

    @task(15)
    def task_get_vets(self):
        self.get_vets()

    @task(5)
    def task_post_owner(self):
        self.post_owner()


class PerfilEscritaUser(PetClinicBaseUser):
    """
    Perfil 2 — Escrita:
    GET /owners:       20%
    GET /owners/{id}:  20%
    GET /vets:         20%
    POST /owners:      40%
    """
    weight = 1

    @task(20)
    def task_get_owners(self):
        self.get_owners()

    @task(20)
    def task_get_owner_by_id(self):
        self.get_owner_by_id()

    @task(20)
    def task_get_vets(self):
        self.get_vets()

    @task(40)
    def task_post_owner(self):
        self.post_owner()


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """
    Discard warmup metrics: after WARMUP_SECONDS, reset all statistics.
    """
    warmup = int(os.environ.get("WARMUP_SECONDS", "60"))
    if warmup > 0:
        def reset_after_warmup():
            gevent.sleep(warmup)
            if environment.runner:
                environment.runner.stats.reset_all()
                print(f"\n[LOCUST-WARMUP] Aquecimento concluido ({warmup}s). Estatisticas reiniciadas para medicao!")
        gevent.spawn(reset_after_warmup)
