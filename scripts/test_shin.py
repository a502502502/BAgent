import penaltyblog as pb

odds = [1.70, 3.50, 5.25]
res_shin = pb.implied.calculate_implied(odds, method="shin")
print("Odds:", odds)
print("Shin implied probabilities:", res_shin)
print("Sum of implied probabilities:", sum(res_shin.get("implied_probabilities", [])))
print("Margin removed:", res_shin.get("margin"))
