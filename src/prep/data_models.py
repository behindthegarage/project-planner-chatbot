class ActivityData:
    def __init__(self, name, description, materials, instructions):
        self.name = name
        self.description = description
        self.materials = materials
        self.instructions = instructions

    def to_dict(self):
        return {
            'name': self.name,
            'description': self.description,
            'materials': self.materials,
            'instructions': self.instructions
        }

