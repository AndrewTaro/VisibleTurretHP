API_VERSION = 'API_v1.0'
MOD_NAME = 'VisibleTurretHP'

DEBUG_MODE = False

class VisibleTurretHP:
    
    def __init__(self):
        with open('log.txt', 'w') as f:
            f.write('Mod {0} loaded. {1}\n\n'.format(MOD_NAME, utils.timeNow()))

        self.OWN_SHIP_ID = None
        self.players = {}
        
        self.gp = GameParamsReader()

        events.onBattleStart(self.get_players) #Create self.players dict
        events.onBattleQuit(self.del_players) #Clear self.players after the battle
        events.onBattleEnd(self.del_players)
        events.onReceiveShellInfo(self.on_receive_shell)
        flash.addExternalCallback('python_log', self.flash_log)
        
        if DEBUG_MODE:
            devmenu.enable()

    def _get_my_id(self):
        me = battle.getSelfPlayerInfo()
        self.OWN_SHIP_ID = me['shipId']

    def del_players(self, *args):
        self.players.clear()

    def get_players(self):
        self._get_my_id()
        players = battle.getPlayersInfo() #<- fuck this function.
        #This returns tons of None while getPlayerInfoBySOMETHING throws back non-None values.
        #I need to use getPlayerInfo again just to get shipComponents.

        for player_id in players:
            player = battle.getPlayerInfo(player_id)

            if player['shipInfo']['subtype'] != 'AirCarrier': #CVs dont have turret            
                ship_id = player['shipId']
                ship = player['shipConfig']['name']
                artillery = player['shipComponents']['artillery']
                hull = player['shipComponents']['hull']
                
                self.players[ship_id] = dict(
                    artillery=self.gp.get_artillery(ship, hull, artillery),
                    name=player['name'],
                    )
        
        if DEBUG_MODE:
            with open('test.json', 'w') as f:
                j = utils.jsonEncode(self.players, indent=4)
                f.write(j)
        
    def on_receive_shell(self, victimId, shooterId, ammoId, matId, shotId, hitType, damage, shotPosition, yaw, hlInfo):
        module_hit = (hitType >> 15) & 0b1 #16th digit

        if damage > 0 and module_hit and victimId in self.players:
            #The last condition: CV players are excluded from dict.
        
            armor_id = matId & 0b11111111
            hl_id = (matId >> 8) & 0b11111111
            
            player = self.players[victimId]
            barbettes = player['artillery']['barbettes']
            
            shell = battle.getAmmoParams(ammoId)
            damage_to_turret = shell.alphaDamage * 0.1
            
            if DEBUG_MODE:
                self.log('victim: {}, armorId: {}, hl_id: {}, damage: {}, hit_type: {}, hl_info: {}, module_id_in_range: {}, armor_id_in_barbette: {}'.format(
                victimId, armor_id, hl_id, damage, hitType, hlInfo, 32>hl_id>0, armor_id in barbettes))
            
            if 32 > hl_id > 0:
                #Main battery has hl_id which starts from 1.
                #estimated it doesn't exceed 32.
                self.turret_damage(damage_to_turret, hl_id, victimId)
                
            elif armor_id in barbettes:
                self.turret_damage(damage_to_turret, barbettes[armor_id], victimId)

    def turret_damage(self, damage, hl_id, vic_id):
        turret = self.players[vic_id]['artillery'][hl_id]
        turret['maxHP'] -= damage
        turret['maxHPwithMod'] -= damage
        turret['receivedDamage'] += damage
        
        flash.call('flash.displayDamage', [hl_id, turret['maxHP'], turret['maxHPwithMod'], turret['receivedDamage'], self.is_self_damage(vic_id)])

    def is_self_damage(self, victim_id):
        return self.OWN_SHIP_ID == victim_id

    def flash_log(self, *args):
        self.log(args)

    def log(self, *args):
        with open('log.txt', 'a') as f:
            f.write('{0}\n'.format(args))
    

class GameParamsReader:
    
    def __init__(self):
        self._gp = None

        with open('ships.json', 'r') as f:
            str_gp = f.read()
            self._gp = utils.jsonDecode(str_gp)

    def _get_guns_params(self, ship, art):
        gp = self._gp[ship][art]
        return {self.__get_turret_id(key): dict(
                    maxHP=gp[key]['HitLocationArtillery']['maxHP'],
                    maxHPwithMod=gp[key]['HitLocationArtillery']['maxHP']*1.5,
                    receivedDamage=0.0,
                    #armor=gp[key]['armor'],
                )
                for key in gp if key.startswith('HP_')}
                
    def __get_turret_id(self, key):
        return int(key[key.rfind('_')+1:])

    def _get_barbettes(self, ship, hull):
        """
        converts {turret: [armor_ids]} to {armor_id: turret_id}
        returns an empty dict if barbettes is {}
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
