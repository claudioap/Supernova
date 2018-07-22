class Period:
    ANNUAL = 1
    FIRST_SEMESTER = 2
    SECOND_SEMESTER = 3
    FIRST_TRIMESTER = 4
    SECOND_TRIMESTER = 5
    THIRD_TRIMESTER = 6
    FOURTH_TRIMESTER = 7

    CHOICES = (
        (ANNUAL, 'Anual'),
        (FIRST_SEMESTER, '1º semestre'),
        (SECOND_SEMESTER, '2º semestre'),
        (FIRST_TRIMESTER, '1º trimestre'),
        (SECOND_TRIMESTER, '2º trimestre'),
        (THIRD_TRIMESTER, '3º trimestre'),
        (FOURTH_TRIMESTER, '4º trimestre'),
    )


class TurnType:
    THEORETICAL = 1
    PRACTICAL = 2
    PRACTICAL_THEORETICAL = 3
    SEMINAR = 4
    TUTORIAL_ORIENTATION = 5
    CHOICES = (
        (THEORETICAL, 'Teórico'),
        (PRACTICAL, 'Teórico'),
        (PRACTICAL_THEORETICAL, 'Teórico-pratico'),
        (SEMINAR, 'Seminário'),
        (TUTORIAL_ORIENTATION, 'Orientação tutorial'),
    )
    ABBREVIATIONS = {
        THEORETICAL: 'T',
        PRACTICAL: 'P',
        PRACTICAL_THEORETICAL: 'TP',
        SEMINAR: 'S',
        TUTORIAL_ORIENTATION: 'OT'
    }

    @staticmethod
    def abbreviation(turn_type):
        if turn_type in TurnType.ABBREVIATIONS:
            return TurnType.ABBREVIATIONS[turn_type]
        return ""


class RoomType:
    GENERIC = 1
    CLASSROOM = 2
    AUDITORIUM = 3
    LABORATORY = 4
    COMPUTER = 5
    MEETING = 6
    MASTERS = 7

    CHOICES = (
        (GENERIC, 'Genérico'),
        (CLASSROOM, 'Sala de aula'),
        (AUDITORIUM, 'Auditório'),
        (LABORATORY, 'Laboratório'),
        (COMPUTER, 'Sala de computadores'),
        (MEETING, 'Sala de reuniões'),
        (MASTERS, 'Sala de mestrados'),
    )


class EvaluationType:
    TEST = 1
    EXAM = 2
    PROJECT = 3

    CHOICES = (
        (TEST, 'Teste'),
        (EXAM, 'Exame'),
        (PROJECT, 'Projeto'),
    )


class FileType:
    IMAGE = 1
    SLIDES = 2
    PROBLEMS = 3
    PROTOCOL = 4
    SEMINAR = 5
    EXAM = 6
    TEST = 7
    SUPPORT = 8
    OTHERS = 9

    CHOICES = (
        (IMAGE, 'Imagem'),
        (SLIDES, 'Slides'),
        (PROBLEMS, 'Problemas'),
        (PROTOCOL, 'Protolos'),
        (SEMINAR, 'Seminário'),
        (EXAM, 'Exame'),
        (TEST, 'Teste'),
        (SUPPORT, 'Suporte'),
        (OTHERS, None),
    )


WEEKDAY_CHOICES = (
    (0, 'Segunda-feira'),
    (1, 'Terça-feira'),
    (2, 'Quarta-feira'),
    (3, 'Quinta-feira'),
    (4, 'Sexta-feira'),
    (5, 'Sábado'),
    (6, 'Domingo')
)


class Degree:
    BACHELORS = 1
    MASTERS = 2
    PHD = 3
    INTEGRATED_MASTERS = 4
    POST_GRADUATION = 5
    ADVANCED_STUDIES = 6
    PRE_GRADUATION = 7

    CHOICES = (
        (BACHELORS, 'Licenciatura'),
        (MASTERS, 'Mestrado'),
        (PHD, 'Doutoramento'),
        (INTEGRATED_MASTERS, 'Mestrado Integrado'),
        (POST_GRADUATION, 'Pos-Graduação'),
        (ADVANCED_STUDIES, 'Estudos Avançados'),
        (PRE_GRADUATION, 'Pré-Graduação'),
    )
    ABBREVIATIONS = {
        BACHELORS: 'L',
        MASTERS: 'M',
        PHD: 'D',
        INTEGRATED_MASTERS: 'Mi',
        POST_GRADUATION: 'Pg',
        ADVANCED_STUDIES: 'EA',
        PRE_GRADUATION: 'pG'
    }

    @staticmethod
    def abbreviation(degree: int):
        if degree in range(0, 7):
            return Degree.ABBREVIATIONS[degree]
        return ""

    @staticmethod
    def name(degree: int):
        if degree in range(1, 8):
            return Degree.CHOICES[degree - 1][1]
        return "Estágio"  # AKA, Nothing, Nilch, Nada