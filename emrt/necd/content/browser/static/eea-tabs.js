jQuery(document).ready(
	function($){
		$(window).bind('eea.tags.loaded', function(evt,tab){
			var $tab=$(tab);
			$tab.find('a').bind('click', function(ev){
				window.location.hash=this.id;
				ev.preventDefault()
			})
		});
		var eea_tabs=function(){
			if($("#whatsnew-gallery").length){return}
			var $eea_tabs=$(".eea-tabs"),eea_tabs_length=$eea_tabs.length,$eea_tabs_panels=$(".eea-tabs-panels"),i=0;
			var $eea_tab,$eea_tabs_panel,$eea_panels,$eea_tab_children;
			if(eea_tabs_length){
				for(i;i<eea_tabs_length;i+=1){
					$eea_tab=$eea_tabs.eq(i);
					if($eea_tab.data('tabs')){
						$(window).trigger('eea.tags.loaded',$eea_tab);
						continue
					}
					$eea_tab.detach();
					$eea_tabs_panel=$eea_tabs_panels.eq(i);
					$eea_panels=$eea_tabs_panel.children();
					$eea_panels.find('.eea-tabs-title').detach().appendTo($eea_tab);
					$eea_tab_children=$eea_tab.children();
					var j=0,tabs_length=$eea_tab_children.length,$tab_title,tab_title_text,tab_title_id;
					for(j;j<tabs_length;j+=1){
						$tab_title=$($eea_tab_children[j]);
						if($tab_title[0].tagName==="P"){
							$tab_title.replaceWith("<li>"+$tab_title.html()+"</li>")
						}
						if(!$tab_title.find('a').length){
							tab_title_text=$tab_title.text();
							tab_title_id=tab_title_text.toLowerCase().replace(/\s/g,'-').replace('&', '');
							$tab_title.text("");
							$('<a />').attr({'href':'#tab-'+tab_title_id,'id':'tab-'+tab_title_id}).html(tab_title_text).appendTo($tab_title)
						}
					}
					$eea_tab_children=$eea_tab.children();
					$eea_tab.tabs($eea_panels);
					$eea_tab.insertBefore($eea_tabs_panel);
					$(window).trigger('eea.tags.loaded',$eea_tab)
				}
			}
		};
		window.EEA=window.EEA||{};
		window.EEA.eea_tabs=eea_tabs;
		eea_tabs();
		$(window).bind('hashchange', function(evt){
			if(window.location.hash.indexOf('tab')!==-1){
				$("#content").find(window.location.hash).click()
			}
		}
	);
	$(window).trigger('eea.tags.loaded',$('#whatsnew-gallery').find('.eea-tabs'));
	$(window).trigger('eea.tags.loaded',$('#multimedia-tabs'));
	if(window.location.hash){
		$(window).trigger('hashchange')}
	}
);

