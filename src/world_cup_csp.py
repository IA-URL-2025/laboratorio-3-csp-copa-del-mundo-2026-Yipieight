import copy

class WorldCupCSP:
    def __init__(self, teams, groups, debug=False):
        """
        Inicializa el problema CSP para el sorteo del Mundial.
        :param teams: Diccionario con los equipos, sus confederaciones y bombos.
        :param groups: Lista con los nombres de los grupos (A-L).
        :param debug: Booleano para activar trazas de depuración.
        """
        self.teams = teams
        self.groups = groups
        self.debug = debug

        # Las variables son los equipos.
        self.variables = list(teams.keys())

        # El dominio de cada variable inicialmente son todos los grupos.
        self.domains = {team: list(groups) for team in self.variables}

    def get_team_confederation(self, team):
        return self.teams[team]["conf"]

    def get_team_pot(self, team):
        return self.teams[team]["pot"]

    def _get_group_teams(self, group, assignment):
        """Retorna la lista de equipos ya asignados a un grupo."""
        return [t for t, g in assignment.items() if g == group]

    def _count_confederation_in_group(self, conf, group_teams):
        """Cuenta cuántos equipos de una confederación hay en un grupo."""
        return sum(1 for t in group_teams if self.get_team_confederation(t) == conf)

    def _has_pot_conflict(self, pot, group_teams):
        """Verifica si ya existe un equipo del mismo bombo en el grupo."""
        return any(self.get_team_pot(t) == pot for t in group_teams)

    def is_valid_assignment(self, group, team, assignment):
        """
        Verifica si asignar un equipo a un grupo viola
        las restricciones de confederación o tamaño del grupo.
        """
        group_teams = self._get_group_teams(group, assignment)

        # Restricción de tamaño: máximo 4 equipos por grupo
        if len(group_teams) >= 4:
            return False

        # Restricción de bombo: no puede haber dos equipos del mismo bombo
        if self._has_pot_conflict(self.get_team_pot(team), group_teams):
            return False

        # Restricción de confederación
        conf = self.get_team_confederation(team)
        conf_count = self._count_confederation_in_group(conf, group_teams)

        if conf == "UEFA":
            # UEFA permite máximo 2 equipos por grupo
            if conf_count >= 2:
                return False
        else:
            # Otras confederaciones: máximo 1 equipo por grupo
            if conf_count >= 1:
                return False

        return True

    def forward_check(self, assignment, domains):
        """
        Propagación de restricciones.
        Debe eliminar valores inconsistentes en dominios futuros.
        Retorna True si la propagación es exitosa, False si algún dominio queda vacío.
        """
        new_domains = copy.deepcopy(domains)

        for team in self.variables:
            if team in assignment:
                continue
            # Filtrar grupos donde la asignación sería inválida
            new_domains[team] = [
                g for g in new_domains[team]
                if self.is_valid_assignment(g, team, assignment)
            ]
            # Si el dominio queda vacío, la propagación falla
            if not new_domains[team]:
                return False, new_domains

        return True, new_domains

    def select_unassigned_variable(self, assignment, domains):
        """
        Heurística MRV (Minimum Remaining Values).
        Selecciona la variable no asignada con el dominio más pequeño.
        """
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            return None
        # Seleccionar la variable con el dominio más pequeño (MRV)
        return min(unassigned, key=lambda v: len(domains[v]))

    def backtrack(self, assignment, domains=None):
        """
        Backtracking search para resolver el CSP.
        """
        if domains is None:
            domains = copy.deepcopy(self.domains)

        # Condición de parada: Si todas las variables están asignadas, retornamos la asignación.
        if len(assignment) == len(self.variables):
            return assignment

        # 1. Seleccionar variable con MRV
        team = self.select_unassigned_variable(assignment, domains)
        if team is None:
            return None

        # 2. Iterar sobre los grupos posibles en el dominio
        for group in domains[team]:
            # 3. Verificar si la asignación es válida
            if self.is_valid_assignment(group, team, assignment):
                # Hacer la asignación
                assignment[team] = group
                if self.debug:
                    print(f"Asignando {team} ({self.get_team_confederation(team)}, Bombo {self.get_team_pot(team)}) -> Grupo {group}")

                # Aplicar forward checking
                success, new_domains = self.forward_check(assignment, domains)

                if success:
                    # 4. Llamada recursiva
                    result = self.backtrack(assignment, new_domains)
                    if result is not None:
                        return result

                # 5. Deshacer la asignación (backtrack)
                del assignment[team]
                if self.debug:
                    print(f"Backtrack: deshaciendo {team} del Grupo {group}")

        return None
