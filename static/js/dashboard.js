$(document).ready(function () {
    // inisialisasi awal
    var start_date;
    var end_date;
  
    // nilai default wordcloud
    let topikWordcloudNeg = $("#selectWordcloudNeg").val();
    let topikWordcloudPos = $("#selectWordcloudPos").val();
  
    // dashboard
    $("#dateRangePicker").daterangepicker(
      {
        showDropdowns: true,
        minYear: 2021,
        maxDate: new Date(),
        startDate: "01/01/2021",
        endDate: moment(),
        opens: "right",
        locale: {
          format: "DD/MM/YYYY",
          separator: " - ",
          daysOfWeek: ["Mg", "Sn", "Sl", "Rb", "Km", "Jm", "Sb"],
          monthNames: [
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
          ],
          firstDay: 1,
        },
      },
      function (start, end) {
        start_date = start.format("YYYY/MM/DD");
        end_date = end.format("YYYY/MM/DD");
        fetchDataDashboard(start_date, end_date);
      }
    );
  
    // fetch min max date based on db
    function fetchMinMaxDate() {
      $.ajax({
        url: "/get_min_max_dates", // URL endpoint yang mengembalikan tanggal min dan max
        type: "GET",
        success: function (data) {
          // format tanggal menjadi 'YYYY/MM/DD'
          start_date = moment(data.min_date).format("YYYY/MM/DD");
          end_date = moment(data.max_date).format("YYYY/MM/DD");
  
          // set tanggal pada saat start halaman awal beranda
          $("#dateRangePicker")
            .data("daterangepicker")
            .setStartDate(moment(data.min_date).format("DD/MM/YYYY"));
          $("#dateRangePicker")
            .data("daterangepicker")
            .setEndDate(moment(data.max_date).format("DD/MM/YYYY"));
  
          fetchDataDashboard(start_date, end_date);
        },
        error: function (XMLHttpRequest, errorThrown) {
          alert("Error: " + errorThrown);
        },
      });
    }
    fetchMinMaxDate();
  
    // fungsi untuk menampilkan figure secara async pada dashboard
    async function showFigure(fig_title, data) {
      Plotly.newPlot(fig_title, JSON.parse(data), { responsive: true });
    }
  
    async function showCuplikanData(start, end) {
      var table = $("#tabelCuplikanKomentar").DataTable({
        processing: true,
        serverSide: true,
        responsive: true,
        paging: true,
        searching: true,
        destroy: true,
        ajax: {
          url: "/dashboard_komentar",
          type: "POST",
          dataType: "json",
          data: function(d) {
              // Menambahkan filter tambahan
              d.start_date = start;
              d.end_date = end
              d.filter_opini = $('#filter').val();

              // Menambahkan informasi entries per page
              d.length = d.length;
          },
        },
        columns: [
          { data: null },
          { data: "komentar" },
          {
            data: "opini",
            className: "text-center",
            render: function (data) {
              let className = "";
              let text = "";
              if (data === 1) {
                className = "badge-primary";
                text = "Opini";
              } else if (data === 0) {
                className = "badge-danger";
                text = "Non Opini";
              } else {
                className = "badge-missing";
                text = "--";
              }
              return `<span class='badge ${className} text-wrap'>${text}</span>`;
            },
          },
          {
            data: "topik",
            className: "text-center",
            render: function (data) {
              let className = "";
              let text = "";
              if (data === 1) {
                className = "badge-primary";
                text = "Isu Waktu Operasional";
              } else if (data === 2) {
                className = "badge-primary";
                text = "Isu Halte";
              } else if (data === 3) {
                className = "badge-primary";
                text = "Isu Rute";
              } else if (data === 4) {
                className = "badge-primary";
                text = "Isu Pembayaran";
              } else if (data === 5) {
                className = "badge-primary";
                text = "Isu Perawatan Bus";
              } else if (data === 6) {
                className = "badge-primary";
                text = "Isu Transit";
              } else if (data === 7) {
                className = "badge-primary";
                text = "Isu Petugas";
              } else if (data === 0) {
                className = "badge-danger";
                text = "Lainnya";
              } else {
                className = "badge-missing";
                text = "--";
              }
              return `<span class='badge ${className} text-wrap'>${text}</span>`;
            },
          },
          {
            data: "sentimen",
            className: "text-center",
            render: function (data) {
              let className = "";
              let text = "";
              if (data === 1) {
                className = "badge-primary";
                text = "Positif";
              } else if (data === 0) {
                className = "badge-danger";
                text = "Negatif";
              } else {
                className = "badge-missing";
                text = "--";
              }
              return `<span class='badge ${className} text-wrap'>${text}</span>`;
            },
          },
        ],
        rowCallback: function (row, data, index) {
          // Add the row number
          var table = $("#tabelCuplikanKomentar").DataTable();
          var info = table.page.info();
          var rowIndex = info.page * info.length + index + 1;
          $("td:eq(0)", row).html(rowIndex);
        },
      });
  
      $("#filter").change(function () {
        table.ajax.reload();
      });
    }
  
    function fetchDataDashboard(start, end) {
      $.ajax({
        url: "/dashboard_data",
        type: "POST",
        data: {
          start_date: start,
          end_date: end,
        },
        success: function (data) {
          if (data.hasOwnProperty("action")) {
            if (data.hasOwnProperty("user")) {
              if (data.user == "auth") {
                // console.log(data)
                Swal.fire({
                  title: "Dashboard",
                  text: data.msg,
                  icon: data.action,
                  showConfirmButton: true,
                  timer: 4000, // tampilkan swal fire selama 4 detik
                }).then(() => {
                  // setelah swal fire ditutup, load
                  window.location.href = "/beranda";
                });
  
                // jika swal fire ditutup sebelum 4 detik, load
                setTimeout(function () {
                  window.location.href = "/beranda";
                }, 4000);
              } else if (data.user == "not_auth") {
                Swal.fire({
                  title: "Dashboard",
                  text: data.msg,
                  icon: data.action,
                  showConfirmButton: true,
                  timer: 4000, // tampilkan swal fire selama 4 detik
                }).then(() => {
                  // setelah swal fire ditutup, load
                  window.location.href = "/login";
                });
  
                // jika swal fire ditutup sebelum 4 detik, load
                setTimeout(function () {
                  window.location.href = "/login";
                }, 4000);
              }
            } else {
              Swal.fire({
                title: "Dashboard",
                text: data.msg,
                icon: data.action,
                showConfirmButton: true,
                timer: 4000, // tampilkan swal fire selama 4 detik
              }).then(() => {
                // setelah swal fire ditutup, load
                location.reload();
              });
  
              // jika swal fire ditutup sebelum 3 detik, load
              setTimeout(function () {
                location.reload();
              }, 4000);
            }
          } else {
            // menampilkan data yang berbentuk angka
            $("#c_kom").text(data.c_kom);
            $("#c_op").text(data.c_op);
            $("#c_nop").text(data.c_nop);
            $("#c_pos").text(data.c_pos);
            $("#c_neg").text(data.c_neg);
  
            // menampilkan data yang berbentuk figure
            showFigure("fig1", data.fig1);
            showFigure("fig2", data.fig2);
            showFigure("fig3", data.fig3);
            showFigure("fig4", data.fig4);
  
            // datatable cuplikan data komentar
            showCuplikanData(start_date, end_date);
  
            fetchWordCloud(start_date, end_date, topikWordcloudNeg);
  
            $(".skeleton").removeClass("skeleton");
          }
        },
        error: function (XMLHttpRequest, errorThrown) {
          alert("Error: " + errorThrown);
        },
      });
    }
  
    // nilai wordcloud ketika berubah
    $("#selectWordcloudNeg").change(function () {
      topikWordcloudNeg = $(this).val();
      fetchWordCloudNeg(start_date, end_date, topikWordcloudNeg);
    });
  
    $("#selectWordcloudPos").change(function () {
      topikWordcloudPos = $(this).val();
      fetchWordCloudPos(start_date, end_date, topikWordcloudPos);
    });
  
    function fetchWordCloudPos(start_date, end_date, topik) {
      $("#wordcloud_pos_alert").addClass("d-none");
      $("#spinnerWordCloudPos").show();
      $("#spinnerWordCloudPos").css("display", "flex");
      $("#wordcloud_pos").addClass("d-none");
  
      $.ajax({
        url: "/wordcloud_pos",
        type: "POST",
        data: {
          start_date: start_date,
          end_date: end_date,
          topik: topik,
        },
        success: function (response) {
          if (response.hasOwnProperty("msg")) {
            $("#wordcloud_pos_alert").text(response.msg);
            $("#wordcloud_pos").addClass("d-none");
            $("#wordcloud_pos_alert").removeClass("d-none");
            $("#spinnerWordCloudPos").hide();
          } else {
            $("#wordcloud_pos").removeClass("d-none");
            $("#wordcloud_pos_alert").addClass("d-none");
            $("#wordcloud_pos").attr(
              "src",
              "data:image/png;base64," + response.wordcloud_pos
            );
            $("#spinnerWordCloudPos").hide();
          }
        },
      });
    }
  
    function fetchWordCloudNeg(start_date, end_date, topik) {
      $("#wordcloud_neg_alert").addClass("d-none");
      $("#spinnerWordCloudNeg").show();
      $("#spinnerWordCloudNeg").css("display", "flex");
      $("#wordcloud_neg").addClass("d-none");
  
      $.ajax({
        url: "/wordcloud_neg",
        type: "POST",
        data: {
          start_date: start_date,
          end_date: end_date,
          topik: topik,
        },
        success: function (response) {
          if (response.hasOwnProperty("msg")) {
            $("#wordcloud_neg_alert").text(response.msg);
            $("#wordcloud_neg").addClass("d-none");
            $("#wordcloud_neg_alert").removeClass("d-none");
            $("#spinnerWordCloudNeg").hide();
          } else {
            $("#wordcloud_neg").removeClass("d-none");
            $("#wordcloud_neg_alert").addClass("d-none");
            $("#wordcloud_neg").attr(
              "src",
              "data:image/png;base64," + response.wordcloud_neg
            );
            $("#spinnerWordCloudNeg").hide();
          }
        },
      });
    }
  
    function fetchWordCloud(start_date, end_date, topik) {
      $("#wordcloud_neg_alert").addClass("d-none");
      $("#spinnerWordCloudNeg").show();
      $("#spinnerWordCloudNeg").css("display", "flex");
      $("#wordcloud_neg").addClass("d-none");
  
      $("#wordcloud_pos_alert").addClass("d-none");
      $("#spinnerWordCloudPos").show();
      $("#spinnerWordCloudPos").css("display", "flex");
      $("#wordcloud_pos").addClass("d-none");
  
      $.ajax({
        url: "/wordcloud",
        type: "POST",
        data: {
          start_date: start_date,
          end_date: end_date,
          topik: topik,
        },
        success: function (response) {
          if (response.hasOwnProperty("msg")) {
            $("#wordcloud_neg_alert").text(response.msg);
            $("#wordcloud_neg").addClass("d-none");
            $("#wordcloud_neg_alert").removeClass("d-none");
            $("#spinnerWordCloudNeg").hide();
  
            $("#wordcloud_pos_alert").text(response.msg);
            $("#wordcloud_pos").addClass("d-none");
            $("#wordcloud_pos_alert").removeClass("d-none");
            $("#spinnerWordCloudPos").hide();
          } else {
            $("#wordcloud_neg").removeClass("d-none");
            $("#wordcloud_neg_alert").addClass("d-none");
            $("#wordcloud_neg").attr(
              "src",
              "data:image/png;base64," + response.wordcloud_pos
            );
            $("#spinnerWordCloudNeg").hide();
  
            $("#wordcloud_pos").removeClass("d-none");
            $("#wordcloud_pos_alert").addClass("d-none");
            $("#wordcloud_pos").attr(
              "src",
              "data:image/png;base64," + response.wordcloud_neg
            );
            $("#spinnerWordCloudPos").hide();
          }
        },
      });
    }
  });
  