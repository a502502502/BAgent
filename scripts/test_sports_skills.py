import sys
sys.stdout.reconfigure(encoding='utf-8')

try:
    import sports_skills
    print("sports_skills imported successfully! Version:", getattr(sports_skills, "__version__", "unknown"))
    print("Dir:", [d for d in dir(sports_skills) if not d.startswith("_")])
except Exception as e:
    print("Error importing sports_skills:", e)

# Test available submodules or functions
try:
    from sports_skills import football
    print("football dir:", [d for d in dir(football) if not d.startswith("_")])
except Exception as e:
    print("football error:", e)

try:
    from sports_skills import espn
    print("espn dir:", [d for d in dir(espn) if not d.startswith("_")])
except Exception as e:
    print("espn error:", e)
