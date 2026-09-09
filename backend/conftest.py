import sys
from pathlib import Path

# Ensure `import app...` resolves regardless of the directory pytest is
# invoked from.
sys.path.insert(0, str(Path(__file__).parent))
