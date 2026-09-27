import json, sqlite3
from pathlib import Path
import pytest
from evaluator.collectors.sql import SQLCollector
from evaluator.collectors.artifact import ArtifactCollector
from evaluator.collectors.security import SecurityCollector
from evaluator.collectors.gpu import GPUCollector
from evaluator.models.candidate import Candidate
from evaluator.models.spec import EvaluationSpec

@pytest.fixture
def candidate(tmp_path):
    (tmp_path/'main.py').write_text('print(1)')
    return Candidate(candidate_id='c1',root=tmp_path,entrypoint='main.py',language='python')

def spec(**configs):
    return EvaluationSpec.model_validate({'evaluation_id':'e1','objective':'x','collector_configs':configs,'fitness':{'metrics':[{'id':'x','source':{'collector':'sql','category':'correctness'},'direction':'maximize','weight':1,'minimum':0,'maximum':1}]}})

@pytest.mark.asyncio
async def test_sql_collector_real_sqlite(candidate):
    s=spec(sql={'setup':['create table t(id integer); insert into t values(1),(2);'],'queries':[{'sql':'select * from t','expected_rows':2}]})
    items=await SQLCollector().collect(candidate,s)
    assert items[0].status.value=='passed' and items[0].value==1

@pytest.mark.asyncio
async def test_artifact_collector_real_file(candidate):
    (candidate.root/'result.json').write_text(json.dumps({'ok':True}))
    s=spec(artifacts={'files':[{'path':'result.json','format':'json'}]})
    items=await ArtifactCollector().collect(candidate,s)
    assert items[0].value==1

@pytest.mark.asyncio
async def test_gpu_collector_never_fakes_missing_gpu(candidate):
    s=spec(gpu={'command':['definitely-not-a-real-gpu-command']})
    item=(await GPUCollector().collect(candidate,s))[0]
    assert item.status.value=='skipped' and item.value is None

@pytest.mark.asyncio
async def test_metric_registry_custom_provider_is_used(candidate):
    from evaluator.metrics import MetricRegistry, CustomMetricProvider
    from evaluator.engine import EvaluationEngine
    from evaluator.models.evidence import Evidence, EvidenceCategory, EvidenceProvenance, EvidenceStatus
    from evaluator.models.spec import EvaluationSpec
    evidence_seen=[]
    def custom(evidence, judgments):
        evidence_seen.extend(evidence)
        return 0.73
    registry=MetricRegistry.canonical()
    registry.register(CustomMetricProvider('custom_quality', custom, version='2.0.0'))
    s=EvaluationSpec.model_validate({'evaluation_id':'custom-e1','objective':'custom','fitness':{'metrics':[{'id':'custom_quality','source':{'collector':'static','category':'static'},'direction':'maximize','weight':1,'minimum':0,'maximum':1}]}})
    class Static:
        name='static'; version='1.0.0'
        async def collect(self,candidate,spec):
            return [Evidence(id='x',collector='static',category=EvidenceCategory.STATIC,status=EvidenceStatus.PASSED,value=1,confidence=1,duration_ms=1,provenance=EvidenceProvenance(candidate_id=candidate.candidate_id,collector_version='1.0.0'))]
    result=await EvaluationEngine([Static()],metric_registry=registry).evaluate(candidate,s)
    assert result.fitness.fitness==0.73
    assert len(evidence_seen)==1
