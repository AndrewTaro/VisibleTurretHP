package VisibleTurretHP
{
   import lesta.api.ModBase;
   
   public class Main extends ModBase
   {
       
      
      private var lastUsedCount:Array;
      
      private var arrayTextFields:Array;
      
      private var arrayActiveTextFields:Array;
      
      private var y_default:Number;
      
      private var x_default:Number;
      
      private const POS_X_OFFSET:Number = 160;
      
      private const POS_Y_OFFSET:Number = 100;
      
      public function Main()
      {
         super();
      }
      
      override public function init() : void
      {
         super.init();
         gameAPI.data.addCallBack("visibleTurretHP.displayDamage",this.displayDamage);
         this.y_default = gameAPI.stage.height / 2 + 5;
         this.x_default = gameAPI.stage.width / 3;
		 this.lastUsedCount = new Array(0,0);
         this.arrayTextFields = new Array(new Array(32),new Array(32));
         this.arrayActiveTextFields = new Array(new CountWithTimer(),new CountWithTimer());
      }
      
      override public function fini() : void
      {
         super.fini();
      }
      
      override public function updateStage(width:Number, height:Number) : void
      {
         super.updateStage(width,height);
      }
      
      public function displayDamage(turretId:Number, maxHP:Number, maxHPWithMod:Number, totalDamage:Number, isSelfDamage:Boolean) : void
      {
         var indice:Number = NaN;
         var tf:TextFieldWithTimer = null;
         var isUpdate:Boolean = false;
         var ct:CountWithTimer = null;
         if(isSelfDamage)
         {
            indice = 0;
         }
         else
         {
            indice = 1;
         }
         ct = this.arrayActiveTextFields[indice];
         if(!(this.arrayTextFields[indice][turretId] is TextFieldWithTimer))
         {
            this.arrayTextFields[indice][turretId] = new TextFieldWithTimer(this.arrayActiveTextFields[indice]);
         }
         tf = this.arrayTextFields[indice][turretId];
         isUpdate = tf.updateValues(turretId,totalDamage,maxHP,maxHPWithMod,isSelfDamage);
         if(!isUpdate)
         {
            if(this.lastUsedCount[indice] == ct.count - 1)
            {
               tf.y = this.y_default + this.POS_Y_OFFSET * ct.count;
               this.lastUsedCount[indice] = ct.count;
            }
            else
            {
               tf.y = this.y_default + this.POS_Y_OFFSET * (ct.count - 1);
               this.lastUsedCount[indice] = ct.count - 1;
            }
         }
         tf.x = this.x_default + this.POS_X_OFFSET * indice;
         gameAPI.stage.addChild(tf);
      }
   }
}

import flash.events.TimerEvent;
import flash.filters.DropShadowFilter;
import flash.text.TextField;
import flash.text.TextFormat;
import flash.utils.Timer;

class TextFieldWithTimer extends TextField
{
    
   
   private var format:TextFormat;
   
   private var timer:Timer;
   
   private var counter:CountWithTimer;
   
   function TextFieldWithTimer(c:CountWithTimer)
   {
      this.format = new TextFormat();
      this.timer = new Timer(6000,1);
      super();
      this.format.size = 15;
      this.defaultTextFormat = this.format;
      this.selectable = false;
      this.timer.addEventListener(TimerEvent.TIMER,this.onTimerEnd);
      this.filters = [new DropShadowFilter()];
      this.width = 180;
      this.height = 100;
      this.text = "";
      this.counter = c;
   }
   
   public function onTimerEnd(e:TimerEvent) : void
   {
      this.counter.count = this.counter.count - 1;
      this.text = "";
      parent.removeChild(this);
   }
   
   public function updateValues(hl_id:Number, totalDamage:Number, HPLeft:Number, HPLeftWithMod:Number, isSelfDamage:Boolean) : Boolean
   {
      var rUpdate:Boolean = false;
      rUpdate = this.isUpdate();
      if(!rUpdate)
      {
         this.counter.count = this.counter.count + 1;
      }
      if(isSelfDamage)
      {
         this.textColor = 16737095;
      }
      else
      {
         this.textColor = 16777215;
      }
      this.text = "Damaged turret: " + hl_id + "\nHP(x1.0): " + HPLeft + "\nHP(x1.5): " + HPLeftWithMod + "\nTotal Damage: " + totalDamage;
      this.timer.reset();
      this.timer.start();
      return rUpdate;
   }
   
   private function isUpdate() : Boolean
   {
      if(this.text == "")
      {
         return false;
      }
      return true;
   }
}

class CountWithTimer
{
    
   
   public var count:Number;
   
   function CountWithTimer()
   {
      super();
      this.count = 0;
   }
}
