import math


class Metrics:

    @staticmethod
    def accuracy(predictions):
        """
        predictions:
            lista di tuple (probability_home, actual_home)

        actual_home:
            1 = Home ha vinto
            0 = Away ha vinto
        """

        if not predictions:
            return 0.0

        correct = 0

        for probability, actual in predictions:

            predicted = 1 if probability >= 0.5 else 0

            if predicted == actual:
                correct += 1

        return correct / len(predictions)

    @staticmethod
    def log_loss(predictions):
        """
        Binary log loss.

        predictions:
            lista di tuple (probability_home, actual_home)
        """

        if not predictions:
            return 0.0

        epsilon = 1e-15

        total = 0.0

        for probability, actual in predictions:

            probability = max(
                epsilon,
                min(1.0 - epsilon, probability)
            )

            if actual == 1:

                total -= math.log(probability)

            else:

                total -= math.log(1.0 - probability)

        return total / len(predictions)

    @staticmethod
    def brier_score(predictions):
        """
        Brier Score binario.

        Più basso = migliore.
        """

        if not predictions:
            return 0.0

        total = 0.0

        for probability, actual in predictions:

            total += (
                probability - actual
            ) ** 2

        return total / len(predictions)