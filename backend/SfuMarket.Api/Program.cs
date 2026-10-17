var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

// Проверка доступности процесса. Подключение к БД появится на следующем этапе.
app.MapGet("/health", () => Results.Ok(new
{
    status = "ok",
    service = "sfu-market",
    version = "0.1.0"
}));

app.Run();
