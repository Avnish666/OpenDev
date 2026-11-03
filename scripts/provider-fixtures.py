"""Generate a NEW private local folder of synthetic acceptance fixtures, never upload."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from app.acceptance.fixtures import generate
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args()
print(json.dumps(generate(args.output_dir),indent=2))
