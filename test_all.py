import pytest

import prometheus

# Test that adding label doesn't actually break the promql query.
#  It's a pretty basic test, but at least the resulting queries have been
#  validated against a prometheus server.
def test_add_label():
    for query in [
        {
            "before": """sum by(instance) (avg_over_time(jvm_memory_used_bytes{kubernetes_pod_name=~".+-service.+"}[5m])) / sum by(instance) (avg_over_time(jvm_memory_max_bytes{kubernetes_pod_name=~"(document|image)-service-.*"}[5m])) > 0.9""",
            "after":  """sum by(instance) (avg_over_time(jvm_memory_used_bytes{p8s_logzio_name="$p8s_logzio_name",kubernetes_pod_name=~".+-service.+"}[5m])) / sum by(instance) (avg_over_time(jvm_memory_max_bytes{p8s_logzio_name="$p8s_logzio_name",kubernetes_pod_name=~"(document|image)-service-.*"}[5m])) > 0.9"""
        },
        {
            "before": """sum(vault_initialized)
  < 0""",
            "after": """sum(vault_initialized{p8s_logzio_name="$p8s_logzio_name"})
  < 0"""
        }
        ]:
        assert(query["after"] == prometheus.add_filter(query["before"], prometheus.LabelFiltering("p8s_logzio_name", "$p8s_logzio_name")))


