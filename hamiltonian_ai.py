class HamiltonianAI:
    def __init__(self, grid_width, grid_height):
        if (grid_width * grid_height) % 2 != 0:
            raise ValueError("Hamiltonian AI kræver et board med et lige antal felter.")

        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cycle = self._build_cycle()
        self.cycle_index = {cell: index for index, cell in enumerate(self.cycle)}

    def _build_cycle(self):
        cycle = []

        for y in range(self.grid_height):
            if y % 2 == 0:
                x_values = range(1, self.grid_width)
            else:
                x_values = range(self.grid_width - 1, 0, -1)

            for x in x_values:
                cycle.append((x, y))

        for y in range(self.grid_height - 1, -1, -1):
            cycle.append((0, y))

        return cycle

    def initial_snake_cells(self):
        return [
            self.cycle[0],
            self.cycle[-1],
            self.cycle[-2],
        ]

    def next_direction(self, head_cell):
        head_index = self.cycle_index[head_cell]
        next_cell = self.cycle[(head_index + 1) % len(self.cycle)]
        return next_cell[0] - head_cell[0], next_cell[1] - head_cell[1]
