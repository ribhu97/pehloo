from pehloo.domain.entities.test_run import TestRun
from pehloo.domain.entities.observation import Observation
from pehloo.domain.ports.i_browser_agent import IBrowserAgent


_STUCK_STATUSES = {"stuck", "failed"}
_MAX_CONSECUTIVE_STUCK = 3


class ExecutePersonaRun:
    def __init__(self, browser_agent: IBrowserAgent) -> None:
        self._browser_agent = browser_agent

    async def execute(self, test_run: TestRun) -> list[Observation]:
        observations: list[Observation] = []
        consecutive_stuck = 0
        try:
            for step in test_run.journey.steps:
                observation = await self._browser_agent.run_step(
                    test_run.persona, step, test_run.target_url
                )
                observations.append(observation)

                if observation.status in _STUCK_STATUSES:
                    consecutive_stuck += 1
                    if consecutive_stuck >= _MAX_CONSECUTIVE_STUCK:
                        break
                else:
                    consecutive_stuck = 0
        finally:
            await self._browser_agent.close()
        return observations
