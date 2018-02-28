from django.core.management.base import BaseCommand, CommandError
from kleep.models import Period, ClipClassInstance, ClassInstance, Class, Turn, TurnInstance, ClipClassroom, Classroom


class Command(BaseCommand):
    help = 'Generates events to match the turn instances'

    def add_arguments(self, parser):
        parser.add_argument('year', nargs='+', type=int)
        parser.add_argument('period', nargs='+', type=int)

    def handle(self, *args, **options):
        year = options['year'][0]
        period = Period.objects.get(id=options['period'][0])

        for clip_classroom in ClipClassroom.objects.all():
            clip_building = clip_classroom.building
            try:
                building = clip_building.building
            except Exception:
                raise CommandError('Please *MANUALLY* link buildings to CLIP buildings before running this.')
            if not hasattr(clip_classroom, 'classroom'):
                corresponding_classroom = Classroom(
                    name=clip_classroom.name, building=building, clip_classroom=clip_classroom)
                corresponding_classroom.save()
                print(f"Created classroom {corresponding_classroom}")

        for clip_class_instance in ClipClassInstance.objects.filter(year=year, period=period):
            clip_class = clip_class_instance.parent
            # Create class in case it doesn't exist
            if hasattr(clip_class, 'related_class'):
                corresponding_class = clip_class.related_class
            else:
                corresponding_class = Class(name=clip_class.name, clip_class=clip_class)
                corresponding_class.save()
                print(f"Created class {corresponding_class}")

            # Create corresponding class instance
            if hasattr(clip_class_instance, 'classinstance'):
                corresponding_class_instance = clip_class_instance.classinstance
            else:
                corresponding_class_instance = ClassInstance(
                    parent=corresponding_class, period=period, year=year, clip_class_instance=clip_class_instance)
                corresponding_class_instance.save()
                print(f"Created class instance {corresponding_class_instance}")

            for clip_turn in clip_class_instance.clipturn_set.all():
                if hasattr(clip_turn, 'turn'):
                    corresponding_turn = clip_turn.turn
                else:
                    corresponding_turn = Turn(clip_turn=clip_turn, turn_type=clip_turn.type, number=clip_turn.number,
                                              class_instance=corresponding_class_instance)
                    corresponding_turn.save()

                for clip_turn_instance in clip_turn.clipturninstance_set.all():
                    if hasattr(clip_turn_instance, 'turninstance'):
                        corresponding_turn_instance = clip_turn_instance.turninstance
                    else:
                        if hasattr(clip_turn_instance, 'start') and hasattr(clip_turn_instance, 'end'):
                            duration = clip_turn_instance.end - clip_turn_instance.start
                        else:
                            duration = None
                        if hasattr(clip_turn_instance, 'classroom'):
                            # ...       ClipTurnInstance   ClipClassroom Classroom
                            classroom = clip_turn_instance.classroom.classroom
                        else:
                            classroom = None

                        corresponding_turn_instance = TurnInstance(
                            turn=corresponding_turn, clip_turn_instance=clip_turn_instance,
                            weekday=clip_turn_instance.weekday, start=clip_turn_instance.start,
                            duration=duration, classroom=classroom)
                        corresponding_turn_instance.save()
                    print(corresponding_turn_instance)
