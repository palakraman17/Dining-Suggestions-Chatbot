function getUrlVars() {
	var vars = {};
	var parts = window.location.href.replace(/[?#&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
			vars[key] = value;
	});
	return vars;
}



var apigClient;
apigClient = apigClientFactory.newClient({});

AWS.config.region = 'us-east-1'; 

var messages = [], //array that hold the record of each string in chat
  lastUserMessage = "", //keeps track of the most recent input string from the user
  botMessage = "", //var keeps track of what the chatbot is going to say
  botName = 'FoodBot', //name of the chatbot
  talking = true; //when false the speach function doesn't work

	function chatbotResponse() {

		return new Promise(function (resolve, reject) {
			talking = true;
			let params = {};
			let additionalParams = {
				headers: {
				"x-api-key" : 'mYVdZgHX193sGTh4XsrN41pMM1kQXwaA4UT62X9u'
				}
			};
			var body = {
			"message" : lastUserMessage
			}
			apigClient.chatbotPost(params, body, additionalParams)
			.then(function(result){
				
				reply = result.data.body;
				reply = reply.substring(1,reply.length-1);
				generate_message(reply,"user");
				
			}).catch( function(result){
				botMessage = "Couldn't connect"
				generate_message(reply,"user");
				reject(result);
			});
		})
	}

	function generate_message(msg, type) {
		INDEX++;
		var str="";
		str += "<div id='cm-msg"+INDEX+"' class=\"chat-msg "+type+"\">";
		str += "        <\/span>";
		str += "          <div class=\"cm-msg-text\">";
		str += msg;
		str += "          <\/div>";
		str += "        <\/div>";
		$(".chat-logs").append(str);
		$("#cm-msg-"+INDEX).hide().fadeIn(300);
		if(type == 'self'){
		 $("#chat-input").val(''); 
		}    
		$(".chat-logs").stop().animate({ scrollTop: $(".chat-logs")[0].scrollHeight}, 1000);    
	  }  


	
	  

function userMessage(msg) {
	lastUserMessage=msg;
};


 
