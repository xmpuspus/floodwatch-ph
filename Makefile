# FloodWatch.PH pipeline targets.
# `make train` + `make hash-verify` reproduce the recurrence classifier
# bit-exact from the committed embeddings cache with NO network, NO GPU.
# The EE-dependent targets (embeddings/event/exposure) regenerate data and
# need Earth Engine credentials: set EE_KEY_FILE to a service-account key
# JSON path (project_id + client_email are read from it). See README.

PY := python3
MODEL := model
EVENT := event
PIPE := pipeline
DATA := site/public/data

EMB := $(MODEL)/embeddings/floodwatch_embeddings_v1.npz
LABELS := $(MODEL)/labels.jsonl
SPLIT := $(MODEL)/holdout_events.json
CLF := $(MODEL)/recurrence_clf_v1.joblib
CAL := $(MODEL)/recurrence_clf_v1_calibration.json

# Canonical sha256 prefix of recurrence_clf_v1.joblib. Set by `make freeze-hash`
# at build time; CI asserts it. Dependency drift changes this — that is the point.
EXPECTED_HASH := b7c702532f92c43f

FC_CACHE := $(PIPE)/_dpwh_flood_control_cache.parquet
FC_ACCT := $(DATA)/flood_control_accountability.json
FC_BYID := $(DATA)/flood_control_by_id.json

.PHONY: all embeddings labels train hash hash-verify calibrate event exposure \
        demo verify test plots freeze-hash clean help \
        flood-control governance-verify

help:
	@echo "FloodWatch.PH targets:"
	@echo "  make embeddings  EE: sample AlphaEarth at labelled points -> npz (network)"
	@echo "  make labels      GFD/CEMS -> recurrence labels + event-disjoint split"
	@echo "  make train       Train recurrence head from cached npz (deterministic, no net)"
	@echo "  make hash-verify Assert recurrence_clf_v1.joblib sha256 == $(EXPECTED_HASH)"
	@echo "  make calibrate   Platt sigmoid on the event-disjoint holdout"
	@echo "  make event       Track A: S1 SAR flood extent for an event (network)"
	@echo "  make exposure    Barangay exposure + official-hazard-gap join"
	@echo "  make demo        Print calibrated bundle + holdout IoU/F1 summary"
	@echo "  make flood-control     Rebuild the governed accountability JSON from the committed parquet cache (deterministic, no net)"
	@echo "  make governance-verify Assert the accountability disclaimer + 337/jargon gates pass"
	@echo "  make verify      Full release gate runner (perm-water, event-disjoint, PII, mirror, hash)"
	@echo "  make test        pytest suite (no network)"
	@echo "  make plots       IoU/PR/reliability figures -> docs/figures/"

all: train calibrate
	@$(MAKE) -s hash-verify
	@echo "[make all] DONE."

# ----- Track B: model (deterministic from committed cache) -----
$(EMB): $(MODEL)/fetch_embeddings.py $(LABELS)
	$(PY) $(MODEL)/fetch_embeddings.py

embeddings: $(EMB)
	@echo "[embeddings] $(EMB) ready"

$(LABELS) $(SPLIT): $(MODEL)/bootstrap_labels.py
	$(PY) $(MODEL)/bootstrap_labels.py

labels: $(LABELS)
	@echo "[labels] $(LABELS) + $(SPLIT) ready"

$(CLF): $(EMB) $(SPLIT) $(MODEL)/train.py
	$(PY) $(MODEL)/train.py

train: $(CLF)
	@echo "[train] $(CLF) ready"

hash:
	@$(PY) -c "import hashlib;print('recurrence_clf_v1.joblib sha256:',hashlib.sha256(open('$(CLF)','rb').read()).hexdigest()[:16])"

hash-verify: $(CLF)
	@actual=$$($(PY) -c "import hashlib;print(hashlib.sha256(open('$(CLF)','rb').read()).hexdigest()[:16])"); \
	if [ "$$actual" = "$(EXPECTED_HASH)" ]; then \
	  echo "[hash-verify] OK: recurrence_clf_v1.joblib sha256 = $$actual"; \
	else \
	  echo "[hash-verify] FAIL: got $$actual, expected $(EXPECTED_HASH)"; \
	  echo "[hash-verify] Likely cause: dependency drift. Honor requirements.txt pins."; \
	  exit 1; \
	fi

freeze-hash: $(CLF)
	@h=$$($(PY) -c "import hashlib;print(hashlib.sha256(open('$(CLF)','rb').read()).hexdigest()[:16])"); \
	sed -i '' "s/^EXPECTED_HASH := .*/EXPECTED_HASH := $$h/" Makefile; \
	echo "[freeze-hash] EXPECTED_HASH := $$h"

$(CAL): $(CLF) $(SPLIT) $(MODEL)/calibrate.py
	$(PY) $(MODEL)/calibrate.py

calibrate: $(CAL)
	@echo "[calibrate] $(CAL) ready"

# ----- Track A: event SAR change-detection (network) -----
event:
	$(PY) $(EVENT)/flood_extent.py --event carina_2024

exposure:
	$(PY) $(PIPE)/exposure.py --event carina_2024
	$(PY) $(PIPE)/hazard_gap.py

demo: $(CAL)
	@$(PY) -c "import json;c=json.load(open('$(CAL)'));print('FloodWatch.PH recurrence_clf_v1');[print(' ',k,'=',v) for k,v in c.get('summary',{}).items()]"

plots:
	$(PY) scripts/plot_metrics.py

# ----- Wave B: flood-control accountability (deterministic from cache) -----
# The committed parquet snapshot IS the deterministic offline artifact, the
# same role the embeddings npz plays for the model. A fresh git checkout
# writes every file with the same mtime, so Make's rebuild decision is
# checkout-order dependent and can fire the network fetch in the adapter.
# Touch the committed cache before the pipeline script so Make treats it as
# up-to-date and the run stays offline and reproducible (mirrors the ci.yml
# model-job touch-in-dependency-order comment).
$(FC_ACCT) $(FC_BYID): $(FC_CACHE) $(PIPE)/flood_control.py \
		floodwatch_ph/accountability/governance.py \
		floodwatch_ph/adapters/flood_control.py
	@touch $(FC_CACHE)
	$(PY) $(PIPE)/flood_control.py

flood-control: $(FC_ACCT) $(FC_BYID)
	@echo "[flood-control] $(FC_ACCT) + $(FC_BYID) regenerated from the committed cache"

governance-verify:
	$(PY) scripts/check_accountability_governance.py
	$(PY) scripts/check_337_collision.py
	$(PY) scripts/check_ai_fingerprints.py
	@echo "[governance-verify] accountability disclaimer + 337 + jargon gates pass"

verify:
	$(PY) scripts/verify_release.py

test:
	pytest tests/ -q

clean:
	rm -f $(CLF) $(CAL)
