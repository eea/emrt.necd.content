jQuery(document).ready(
	function($) {
    const setCurrentTab = () => {
      const allTabPanels = $(".eea-tabs-panel");
      allTabPanels.hide();

      let requestedPanel = window.location.hash ? $(document).find(window.location.hash) : null;
      if (!requestedPanel) {
        requestedPanel = allTabPanels.first();
      }

      requestedPanel.show();

      const requestedTabId = requestedPanel.attr('id')

      $(".eea-tabs > div").removeClass("active");
      $(`.eea-tabs a[href="#${requestedTabId}"]`).parent().addClass("active");
    }
    setCurrentTab();
    $(window).bind('hashchange', setCurrentTab);
  });

