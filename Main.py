API_VERSION = 'API_v1.0'
MOD_NAME = 'VisibleTurretHP'

DEBUG_MODE = False

class VisibleTurretHP:
    SHIPS_WITHOUT_MAINGUN = ['AirCarrier', 'Auxiliary']
    
    def __init__(self):
        self.players = {}        
        self.gp = GameParamsReader()
        self.register_events()
        
        if DEBUG_MODE:
            devmenu.enable()
            
    def register_events(self):
        events.onBattleStart(self.get_players) #Creates self.players dict when the battle starts
        events.onBattleQuit(self.del_players) #Clears self.players after the battle ends
        events.onBattleEnd(self.del_players)
        events.onReceiveShellInfo(self.on_receive_shell)

    def del_players(self, *args):
        self.players.clear()

    def get_players(self):
        players = battle.getPlayersInfo()
        #This returns tons of None while getPlayerInfoBySOMETHING throws back non-None values.
        #I need to use getPlayerInfo again just to get shipComponents.

        for player_id in players:
            player = battle.getPlayerInfo(player_id)

            if player['shipInfo']['subtype'] not in self.SHIPS_WITHOUT_MAINGUN: #CV/Auxiliary don't have turret
                ship_id = player['shipId']
                ship = player['shipConfig']['name']
                artillery = player['shipComponents']['artillery']
                hull = player['shipComponents']['hull']
                
                self.players[ship_id] = dict(
                    artillery=self.gp.get_artillery(ship, hull, artillery),
                    name=player['name'],
                    )
        
        if DEBUG_MODE:
            with open('players.json', 'w') as f:
                j = utils.jsonEncode(self.players, indent=4)
                f.write(j)
        
    def on_receive_shell(self, victimId, shooterId, ammoId, matId, shotId, hitType, damage, shotPosition, yaw, hlInfo):
        module_hit = (hitType >> 15) & 0b1 #16th digit

        if damage > 0 and module_hit and victimId in self.players:
            #The last condition: SHIPS_WITHOUT_MAINGUN are excluded from dict.
        
            armor_id = matId & 0b11111111
            hl_id = (matId >> 8) & 0b11111111
            turret_id = None
            barbettes = self.players[victimId]['artillery']['barbettes']
            
            shell = battle.getAmmoParams(ammoId)
            damage_to_turret = shell.alphaDamage * 0.1
            is_incoming = bool(hitType & 0b1)
            
            if DEBUG_MODE:
                self.log('victim: {}, armorId: {}, hl_id: {}, damage: {}, hit_type: {}, hl_info: {}, module_id_in_range: {}, armor_id_in_barbette: {}'.format(
                victimId, armor_id, hl_id, damage, hitType, hlInfo, 32>hl_id>0, armor_id in barbettes))
            
            if 32 > hl_id > 0:
                #Main battery has hl_id which starts from 1.
                #estimated it doesn't exceed 32.
                turret_id = hl_id
                
            elif armor_id in barbettes:
                turret_id = barbettes[armor_id]
                
            if turret_id is not None:
                self.turret_damage(damage_to_turret, turret_id, victimId, is_incoming)

    def turret_damage(self, damage, hl_id, vic_id, is_incoming):
        turret = self.players[vic_id]['artillery'][hl_id]
        turret['maxHP'] -= damage
        turret['maxHPwithMod'] -= damage
        turret['receivedDamage'] += damage
        
        flash.call('visibleTurretHP.displayDamage', [hl_id, turret['maxHP'], turret['maxHPwithMod'], turret['receivedDamage'], is_incoming])

    def log(self, *args, **kargs):
        with open('log.txt', 'a') as f:
            f.write('{} | {}, {}\n'.format(utils.timeNow(), args, kargs))
    

class GameParamsReader:
    GAMEPARAMS_FILENAMES = ['turretHP_and_barbettes.json', 'ships.json']
    
    def __init__(self):
        self._gp = None
        self._load_file()
            
    def _load_file(self):
        for filename in self.GAMEPARAMS_FILENAMES:
            try:
                with open(filename, 'r') as f:
                    self._gp = utils.jsonDecode(f.read())
                    break
            except:
                continue

    def _get_guns_params(self, ship, art):
        gp = self._gp[ship][art]
        return {self.__get_turret_id(key): dict(
                    maxHP=gp[key]['HitLocationArtillery']['maxHP'],
                    maxHPwithMod=gp[key]['HitLocationArtillery']['maxHP']*1.5,
                    receivedDamage=0.0,
                )
                for key in gp if key.startswith('HP_')}
                
    def __get_turret_id(self, key):
        return int(key[key.rfind('_')+1:])

    def _get_barbettes(self, ship, hull):
        """
        converts {turret: [armor_ids]} to {armor_id: turret_id}
        returns an empty dict if barbettes are {}
        """
        barbettes = self._gp[ship][hull]['barbettes']
        return {
                armor_id & 0b11111111 : self.__get_turret_id(turret)
                for turret in barbettes
                for armor_id in barbettes[turret]
               }

    def get_artillery(self, ship, hull, art):
        return dict(
                self._get_guns_params(ship, art),
                barbettes=self._get_barbettes(ship, hull)
               )


turretHP = VisibleTurretHP()
